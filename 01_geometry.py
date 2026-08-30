#!/usr/bin/env python3
"""
FAZ 1: Geometri ve Footprint Çıkarımı Test Scripti
OpenCV + PaddleOCR kullanarak manga/manhwa yazı bloklarını tespit eder.
"""

import cv2
import numpy as np
import json
import os
import sys
from pathlib import Path

try:
    from paddleocr import PaddleOCR
except ImportError:
    print("❌ PaddleOCR bulunamadı. 'pip install paddlepaddle paddleocr' ile yükleyin.")
    sys.exit(1)

# OCR modelini başlat (İngilizce - manga için optimize)
ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)

def extract_geometry(image_path: str, output_dir: str = "output"):
    """
    Görüntüdeki yazı bloklarının geometrisini çıkarır.
    
    Args:
        image_path: Giriş görsel yolu
        output_dir: Çıktı klasörü
    
    Returns:
        geometry_data: JSON formatında geometri verileri
    """
    # Görüntüyü yükle
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Görüntü yüklenemedi: {image_path}")
        return None
    
    original_height, original_width = img.shape[:2]
    print(f"[i] Görüntü boyutu: {original_width}x{original_height}")
    
    # Ölçeklendirme (büyük görseller için)
    max_dim = 2000
    scale = 1.0
    if max(original_width, original_height) > max_dim:
        scale = max_dim / max(original_width, original_height)
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)
        img_resized = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
        print(f"[i] Ölçeklendirildi: {scale:.2f} -> {new_width}x{new_height}")
    else:
        img_resized = img
    
    # OCR çalıştır
    result = ocr.ocr(img_resized, cls=True)[0]
    
    if not result:
        print("[!] Hiçbir yazı bloğu tespit edilemedi.")
        return {"width": original_width, "height": original_height, "block_count": 0, "blocks": []}
    
    blocks = []
    for idx, line in enumerate(result):
        if line is None or len(line) < 2:
            continue
        
        bbox_points = line[0]  # 4 köşe noktası
        text = line[1][0]       # Metin içeriği
        confidence = line[1][1] # Güven skoru
        
        # Numpy array'e çevir
        pts = np.array(bbox_points, dtype=np.float32)
        
        # Orijinal boyutlara geri ölçeklendir
        pts = pts / scale
        
        # minAreaRect hesapla
        rect = cv2.minAreaRect(pts)
        center, size, angle = rect
        width_rect, height_rect = size
        
        # Polygon mask oluştur
        mask = np.zeros((original_height, original_width), dtype=np.uint8)
        pts_int = pts.astype(np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(mask, [pts_int], 255)
        
        # Footprint metrikleri
        area = cv2.contourArea(pts_int)
        aspect_ratio = width_rect / max(height_rect, 1)
        pixel_count = cv2.countNonZero(mask)
        chars = len(text)
        pixel_per_char = pixel_count / max(chars, 1)
        
        block_data = {
            "id": idx,
            "text": text,
            "confidence": confidence,
            "center": [float(center[0]), float(center[1])],
            "size": [float(width_rect), float(height_rect)],
            "angle": float(angle),
            "polygon": [[float(p[0]), float(p[1])] for p in pts],
            "area": float(area),
            "aspect_ratio": float(aspect_ratio),
            "pixel_count": int(pixel_count),
            "chars": chars,
            "pixel_per_char": float(pixel_per_char),
            "mask_file": f"masks/block_{idx:03d}.png"
        }
        blocks.append(block_data)
    
    # Debug görseli oluştur
    debug_img = img.copy()
    for block in blocks:
        pts = np.array(block["polygon"], dtype=np.int32)
        
        # Polygon çiz (yeşil)
        cv2.polylines(debug_img, [pts], True, (0, 255, 0), 2)
        
        # Merkez noktası (mavi)
        cx, cy = int(block["center"][0]), int(block["center"][1])
        cv2.circle(debug_img, (cx, cy), 5, (255, 0, 0), -1)
        
        # ID yazdır
        cv2.putText(debug_img, f"#{block['id']}", (cx - 20, cy - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (128, 0, 128), 2)
    
    # Çıktı klasörlerini oluştur
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "debug"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "results"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "results", "masks"), exist_ok=True)
    
    # Debug görselini kaydet
    base_name = Path(image_path).stem
    debug_path = os.path.join(output_dir, "debug", f"{base_name}_detections.png")
    cv2.imwrite(debug_path, debug_img)
    print(f"[✓] Debug görseli: {debug_path}")
    
    # Maskeleri kaydet
    for block in blocks:
        mask = np.zeros((original_height, original_width), dtype=np.uint8)
        pts = np.array(block["polygon"], dtype=np.int32)
        cv2.fillPoly(mask, [pts], 255)
        
        mask_path = os.path.join(output_dir, "results", "masks", f"block_{block['id']:03d}.png")
        cv2.imwrite(mask_path, mask)
    
    # JSON sonuçlarını hazırla
    geometry_data = {
        "source_image": image_path,
        "width": original_width,
        "height": original_height,
        "block_count": len(blocks),
        "blocks": blocks
    }
    
    # JSON'u kaydet
    json_path = os.path.join(output_dir, "results", f"{base_name}_geometry.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(geometry_data, f, indent=2, ensure_ascii=False)
    print(f"[✓] JSON sonuçları: {json_path}")
    
    return geometry_data


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python 01_geometry.py <görsel_yolu> [çıktı_klasörü]")
        print("Örnek: python 01_geometry.py test_images/sample.png output")
        sys.exit(1)
    
    image_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"
    
    print("=" * 60)
    print("FAZ 1: GEOMETRİ VE FOOTPRINT ÇIKARIMI")
    print("=" * 60)
    
    result = extract_geometry(image_path, output_dir)
    
    if result:
        print("\n" + "=" * 60)
        print(f"TOPLAM {result['block_count']} YAZI BLOĞU TESPİT EDİLDİ")
        print("=" * 60)
        
        for block in result['blocks']:
            print(f"\n📦 Blok #{block['id']}")
            print(f"   Metin: \"{block['text'][:50]}...\" ({block['chars']} karakter)")
            print(f"   Konum: ({block['center'][0]:.1f}, {block['center'][1]:.1f})")
            print(f"   Boyut: {block['size'][0]:.1f} x {block['size'][1]:.1f}")
            print(f"   Açı: {block['angle']:.2f}°")
            print(f"   Alan: {block['area']:.1f} px²")
            print(f"   Güven: %{block['confidence']:.1f}")
    else:
        print("❌ İşlem başarısız!")
        sys.exit(1)
