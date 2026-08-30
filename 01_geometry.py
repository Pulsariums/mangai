"""
FAZ 1: Geometri ve Ayak İzi (Footprint) Çıkarımı

Bu modül, manga/manhwa sayfalarındaki yazı bloklarını tespit eder.
Her yazı bloğu için:
- minAreaRect (açı, genişlik, yükseklik, merkez)
- polygon_mask
- safe_area_mask
çıkarır.

Kullanılan Teknolojiler:
- OCR: PaddleOCR (manga-ocr alternatifi)
- Geometri: OpenCV
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
import numpy as np
import cv2

# Proje kökünü path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import (
    load_config, 
    ensure_dirs, 
    polygon_to_mask, 
    min_area_rect_from_polygon,
    merge_nearby_boxes,
    calculate_footprint_metrics,
    save_debug_image
)


class GeometryExtractor:
    """
    Yazı bloklarının geometrik özelliklerini çıkaran sınıf
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ocr = None
        self._init_ocr()
    
    def _init_ocr(self):
        """OCR motorunu başlat"""
        ocr_config = self.config.get('ocr', {})
        provider = ocr_config.get('provider', 'paddleocr')
        
        if provider == 'paddleocr':
            try:
                from paddleocr import PaddleOCR
                
                # PaddleOCR'u başlat
                # use_textline_orientation: Açı sınıflandırması kullan (eğik metinler için)
                # lang: Dil (en, ja, ko)
                # Not: Yeni PaddleOCR versiyonlarında bazı parametreler değişti
                self.ocr = PaddleOCR(
                    use_textline_orientation=ocr_config.get('use_angle_cls', True),
                    lang=ocr_config.get('lang', 'en'),
                    text_det_thresh=ocr_config.get('det_db_thresh', 0.3),
                    text_det_box_thresh=ocr_config.get('det_db_box_thresh', 0.5),
                    text_det_unclip_ratio=ocr_config.get('det_db_unclip_ratio', 1.6)
                )
                print("[✓] PaddleOCR başarıyla başlatıldı")
                
            except ImportError:
                print("[!] PaddleOCR bulunamadı. Kurulum gerekli:")
                print("    pip install paddlepaddle paddleocr")
                raise
        else:
            raise ValueError(f"Desteklenmeyen OCR sağlayıcı: {provider}")
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Görüntüyü OCR için ön işle
        Performans için boyutu optimize et
        """
        img_config = self.config.get('image', {})
        max_width = img_config.get('max_width', 2000)
        max_height = img_config.get('max_height', 3000)
        
        h, w = image.shape[:2]
        
        # Çok büyükse ölçeklendir
        scale = 1.0
        if w > max_width or h > max_height:
            scale = min(max_width / w, max_height / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            print(f"[i] Görüntü ölçeklendirildi: {w}x{h} -> {new_w}x{new_h} (scale: {scale:.2f})")
        
        return image, scale
    
    def extract_text_blocks(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Görüntüdeki tüm yazı bloklarını çıkar
        
        Returns:
            Her biri şu bilgileri içeren dict listesi:
            - id: Benzersiz ID
            - text: OCR ile okunan metin
            - confidence: Güven skoru
            - polygon: Köşe noktaları (4, 2)
            - rect: minAreaRect bilgileri
            - mask: Binary maske
        """
        # Ön işleme
        processed_img, scale = self.preprocess_image(image)
        
        # OCR çalıştır (PaddleOCR 2.7.x API: ocr() kullan)
        result = self.ocr.ocr(processed_img, cls=False)
        
        text_blocks = []
        block_id = 0
        
        # PaddleOCR sonucu parse et
        # Result format: [[[box], (text, confidence)], ...]
        if not result or not result[0]:
            print("[!] OCR sonucu boş")
            return []
        
        for line in result[0]:
            if not line or len(line) < 2:
                continue
            
            box = np.array(line[0], dtype=np.int32)
            text, confidence = line[1]
            
            # Boş metni atla
            if not text or not text.strip():
                continue
            
            # Güven skoru düşükse atla
            if confidence < 0.5:
                continue
            
            # Box'ı düzelt (PaddleOCR bazen düzgün vermez)
            if len(box) != 4:
                # minAreaRect ile düzelt
                rect = cv2.minAreaRect(box.astype(np.float32))
                box = cv2.boxPoints(rect).astype(np.int32)
            
            # Maske oluştur
            height, width = processed_img.shape[:2]
            mask = polygon_to_mask(box, height, width)
            
            # Footprint metriklerini hesapla
            footprint = calculate_footprint_metrics(box, text)
            
            # Orijinal ölçekte düzelt
            if scale != 1.0:
                box = (box / scale).astype(np.int32)
                mask = cv2.resize(mask, (image.shape[1], image.shape[0]), 
                                interpolation=cv2.INTER_NEAREST)
                footprint['rect']['center'] = tuple(c / scale for c in footprint['rect']['center'])
                footprint['rect']['size'] = tuple(s / scale for s in footprint['rect']['size'])
                footprint['area'] = footprint['area'] / (scale * scale)
            
            text_blocks.append({
                'id': block_id,
                'text': text,
                'confidence': confidence,
                'polygon': box.tolist(),
                'rect': footprint['rect'],
                'mask': mask,
                'footprint': footprint,
                'original_image_size': (image.shape[1], image.shape[0])  # (width, height)
            })
            
            block_id += 1
        
        print(f"[✓] {len(text_blocks)} yazı bloğu tespit edildi")
        return text_blocks
    
    def merge_into_lines(self, text_blocks: List[Dict], threshold: float = None) -> List[Dict]:
        """
        Bitişik kutuları satır halinde birleştir
        Manga'da aynı satırdaki kelimeler ayrı algılanabilir
        """
        if threshold is None:
            threshold = self.config.get('geometry', {}).get('merge_line_distance', 10.0)
        
        if len(text_blocks) <= 1:
            return text_blocks
        
        # Kutuları topla
        boxes = [np.array(block['polygon']) for block in text_blocks]
        
        # Birleştir
        merged_boxes = merge_nearby_boxes(boxes, threshold)
        
        print(f"[i] Satır birleştirme: {len(boxes)} -> {len(merged_boxes)} blok")
        
        # Yeni blokları oluştur (basitleştirilmiş)
        # Not: Gerçek implementasyonda metinleri de birleştirmek gerekir
        # Bu Faz 1 için şimdilik kutu birleştirme yeterli
        return text_blocks  # Şimdilik değiştirmeden döndür
    
    def draw_detections(self, image: np.ndarray, text_blocks: List[Dict]) -> np.ndarray:
        """
        Tespit edilen blokları görselleştir
        - Kırmızı: minAreaRect kutuları
        - Yeşil: Polygon sınırları
        - Mavi: Merkez noktaları
        """
        output = image.copy()
        output_config = self.config.get('output', {})
        rect_color = tuple(output_config.get('rect_color', [255, 0, 0]))  # BGR
        rect_thickness = output_config.get('rect_thickness', 2)
        
        for block in text_blocks:
            # Polygon'u al
            polygon = np.array(block['polygon'], dtype=np.int32)
            
            # minAreaRect kutusunu al
            box = np.array(block['rect']['box'], dtype=np.int32)
            
            # 1. Polygon çiz (yeşil, ince)
            cv2.drawContours(output, [polygon], -1, (0, 255, 0), 1)
            
            # 2. minAreaRect çiz (kırmızı, kalın)
            cv2.drawContours(output, [box], -1, rect_color, rect_thickness)
            
            # 3. Merkez noktası (mavi)
            center = tuple(int(x) for x in block['rect']['center'])
            cv2.circle(output, center, 4, (255, 0, 0), -1)
            
            # 4. ID ve açı bilgisi
            angle = block['rect']['angle']
            label = f"#{block['id']} {angle:.1f}°"
            cv2.putText(output, label, (box[0][0], box[0][1] - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        return output
    
    def process_image(self, image_path: str, save_results: bool = True) -> Dict[str, Any]:
        """
        Tek bir görüntüyü işle ve sonuçları kaydet
        
        Returns:
            İşleme sonuçlarını içeren dict
        """
        print(f"\n{'='*60}")
        print(f"İŞLENİYOR: {image_path}")
        print(f"{'='*60}\n")
        
        # Görüntüyü yükle
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Görüntü bulunamadı: {image_path}")
        
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Görüntü yüklenemedi: {image_path}")
        
        original_size = (image.shape[1], image.shape[0])
        print(f"[i] Görüntü boyutu: {original_size[0]}x{original_size[1]}")
        
        # Yazı bloklarını çıkar
        text_blocks = self.extract_text_blocks(image)
        
        # Satır birleştirme (opsiyonel)
        # text_blocks = self.merge_into_lines(text_blocks)
        
        # Görselleştir
        debug_image = self.draw_detections(image, text_blocks)
        
        # Sonuçları kaydet
        results = {
            'image_path': image_path,
            'original_size': original_size,
            'text_blocks': text_blocks,
            'block_count': len(text_blocks)
        }
        
        if save_results:
            output_config = self.config.get('output', {})
            debug_dir = output_config.get('debug_dir', './output/debug')
            results_dir = output_config.get('results_dir', './output/results')
            
            # Dosya adını oluştur
            base_name = Path(image_path).stem
            
            # Debug görselini kaydet
            debug_path = os.path.join(debug_dir, f"{base_name}_detections.png")
            save_debug_image(debug_image, debug_path)
            print(f"[✓] Debug görseli kaydedildi: {debug_path}")
            
            # JSON sonuçları kaydet
            json_path = os.path.join(results_dir, f"{base_name}_geometry.json")
            
            # Maskeleri numpy array'den list'e çevir (JSON serializable için)
            serializable_blocks = []
            for block in text_blocks:
                block_copy = block.copy()
                block_copy['mask'] = block_copy['mask'].tolist()  # Mask'i listeye çevir
                serializable_blocks.append(block_copy)
            
            results['text_blocks'] = serializable_blocks
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"[✓] JSON sonuçları kaydedildi: {json_path}")
            
            # İsteğe bağlı: Maskeleri ayrı kaydet
            if output_config.get('save_masks', True):
                masks_dir = os.path.join(debug_dir, f"{base_name}_masks")
                Path(masks_dir).mkdir(parents=True, exist_ok=True)
                
                for block in text_blocks:
                    mask_path = os.path.join(masks_dir, f"block_{block['id']}_mask.png")
                    save_debug_image(block['mask'], mask_path)
                
                print(f"[✓] {len(text_blocks)} adet maske kaydedildi: {masks_dir}")
        
        return results


def main():
    """
    Ana giriş noktası
    """
    parser = argparse.ArgumentParser(
        description='FAZ 1: Manga/Manhwa Geometri ve Footprint Çıkarımı'
    )
    parser.add_argument(
        'input',
        type=str,
        help='Girdi görüntü dosyası veya klasörü'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Konfigürasyon dosyası (varsayılan: config.yaml)'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Sonuçları kaydetme (sadece ekrana yazdır)'
    )
    
    args = parser.parse_args()
    
    # Konfigürasyonu yükle
    print("[i] Konfigürasyon yükleniyor...")
    config = load_config(args.config)
    
    # Klasörleri oluştur
    ensure_dirs(config)
    
    # GeometryExtractor'ı başlat
    extractor = GeometryExtractor(config)
    
    # Girdiyi işle (tek dosya veya klasör)
    input_path = args.input
    
    if os.path.isfile(input_path):
        # Tek dosya
        extractor.process_image(input_path, save_results=not args.no_save)
    elif os.path.isdir(input_path):
        # Klasör
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
        image_files = [
            f for f in os.listdir(input_path)
            if os.path.isfile(os.path.join(input_path, f)) and
            os.path.splitext(f)[1].lower() in image_extensions
        ]
        
        print(f"\n[i] Klasörde {len(image_files)} görüntü bulundu")
        
        for i, filename in enumerate(sorted(image_files), 1):
            filepath = os.path.join(input_path, filename)
            print(f"\n[{i}/{len(image_files)}] İşleniyor: {filename}")
            
            try:
                extractor.process_image(filepath, save_results=not args.no_save)
            except Exception as e:
                print(f"[!] Hata: {e}")
                continue
    else:
        print(f"[!] Geçersiz girdi: {input_path}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print("FAZ 1 TAMAMLANDI")
    print(f"{'='*60}\n")
    print("Sonraki adım: Çıkarılan geometry.json dosyalarını inceleyin.")
    print("Test etmek için: python 01_geometry.py test_images/sample.png --no-save\n")


if __name__ == '__main__':
    main()
