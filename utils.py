"""
Ortak yardımcı fonksiyonlar ve utility fonksiyonları
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Konfigürasyon dosyasını yükle"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def ensure_dirs(config: Dict[str, Any]):
    """Gerekli çıktı klasörlerini oluştur"""
    dirs_to_create = [
        config['output']['debug_dir'],
        config['output']['results_dir'],
        os.path.dirname(config['cache']['db_path']),
        os.path.dirname(config['cache']['glossary_path'])
    ]
    
    for dir_path in dirs_to_create:
        if dir_path:
            Path(dir_path).mkdir(parents=True, exist_ok=True)


def polygon_to_mask(polygon: np.ndarray, height: int, width: int) -> np.ndarray:
    """Polygon koordinatlarından binary maske oluştur"""
    from PIL import Image, ImageDraw
    
    mask = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(mask)
    
    # Polygon'u integer'a çevir
    poly_points = [(int(x), int(y)) for x, y in polygon]
    draw.polygon(poly_points, fill=255)
    
    return np.array(mask)


def min_area_rect_from_polygon(polygon: np.ndarray) -> Dict[str, Any]:
    """
    Polygon'dan minimum alan dikdörtgeni bilgilerini çıkar
    OpenCV'nin minAreaRect formatıyla uyumlu
    """
    import cv2
    
    # Float32 array'e çevir
    points = polygon.astype(np.float32)
    
    # Minimum alan dikdörtgenini bul
    rect = cv2.minAreaRect(points)
    (center_x, center_y), (width, height), angle = rect
    
    # Köşe noktalarını hesapla
    box = cv2.boxPoints(rect)
    box = np.int0(box)
    
    return {
        'center': (center_x, center_y),
        'size': (width, height),
        'angle': angle,
        'box': box,
        'area': width * height
    }


def merge_nearby_boxes(boxes: List[np.ndarray], threshold: float = 10.0) -> List[np.ndarray]:
    """
    Yakın kutuları birleştir (satır oluşturma için)
    boxes: Her biri (4, 2) shape'inde köşe noktaları içeren liste
    """
    if not boxes:
        return []
    
    import cv2
    
    merged = []
    used = set()
    
    for i, box1 in enumerate(boxes):
        if i in used:
            continue
            
        current_box = box1
        changed = True
        
        while changed:
            changed = False
            for j, box2 in enumerate(boxes):
                if j in used or j == i:
                    continue
                
                # Merkezler arası mesafe
                center1 = np.mean(current_box, axis=0)
                center2 = np.mean(box2, axis=0)
                distance = np.linalg.norm(center1 - center2)
                
                if distance < threshold:
                    # Birleştir: Tüm noktaları al ve yeni minAreaRect hesapla
                    all_points = np.vstack([current_box, box2])
                    current_box = cv2.minAreaRect(all_points.astype(np.float32))
                    current_box = cv2.boxPoints(current_box)
                    used.add(j)
                    changed = True
        
        used.add(i)
        merged.append(current_box.astype(np.int0))
    
    return merged


def calculate_footprint_metrics(polygon: np.ndarray, text_content: str) -> Dict[str, Any]:
    """
    Yazı bloğunun footprint (ayak izi) metriklerini hesapla
    Bu bilgiler render aşamasında kullanılacak
    """
    rect_info = min_area_rect_from_polygon(polygon)
    
    # Piksel yoğunluğu (metin uzunluğuna göre)
    area = rect_info['area']
    char_count = len(text_content)
    pixels_per_char = area / char_count if char_count > 0 else 0
    
    # En-boy oranı
    width, height = rect_info['size']
    aspect_ratio = width / height if height > 0 else 0
    
    return {
        'polygon': polygon.tolist(),
        'rect': {
            'center': rect_info['center'],
            'size': rect_info['size'],
            'angle': rect_info['angle'],
            'box': rect_info['box'].tolist()
        },
        'area': area,
        'aspect_ratio': aspect_ratio,
        'pixels_per_char': pixels_per_char,
        'original_text': text_content,
        'char_count': char_count
    }


def save_debug_image(image: np.ndarray, filepath: str):
    """Debug görselini kaydet"""
    import cv2
    
    # BGR'den RGB'ye çevir (eğer gerekliyse)
    if len(image.shape) == 3 and image.shape[2] == 3:
        # OpenCV BGR kullanır, PNG kaydı için RGB'ye çevir
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        cv2.imwrite(filepath, image_rgb)
    else:
        cv2.imwrite(filepath, image)


def extract_text_color(image: np.ndarray, mask: np.ndarray) -> Dict[str, Any]:
    """
    Maske içindeki piksellerden ortalama metin rengini çıkar
    Render aşamasında kullanılacak
    """
    import cv2
    
    # Maskeyi binary yap
    _, binary_mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    
    # Maskelenmiş bölgelerin ortalamasını al
    mean_val = cv2.mean(image, mask=binary_mask)[:3]
    
    return {
        'mean_color': mean_val,  # BGR formatında
        'hex_color': '#{:02x}{:02x}{:02x}'.format(
            int(mean_val[2]), int(mean_val[1]), int(mean_val[0])
        )
    }
