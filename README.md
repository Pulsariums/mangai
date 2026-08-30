# Manga/Manhwa Otomatik Çeviri ve Typesetting Pipeline

Bu proje, manga ve manhwa sayfalarını otomatik olarak çevirmek ve orijinal yazıların yerine yeni metni yerleştirmek için geliştirilmiştir.

## 🎯 Temel Felsefe

1. **Optik Merkez Yalanı:** Yazıyı balonun ortasına hizalamıyoruz. Eski yazının kapladığı bölge (Footprint) tespit ediliyor ve yeni metin **tam olarak o footprint'in içine** yerleştiriliyor.

2. **Doku Taklidi (İnpainting):** Balon içi düz beyaz boya ile doldurulmuyor. Gradient, screentone veya renkli arka planlar lokal algoritmalar (LaMa, PatchMatch) ile korunuyor.

3. **Bağlamsal Çeviri:** Metinler balon balon değil, bölüm bazlı JSON formatında, Glossary ve Character Memory ile birlikte LLM'e gönderiliyor.

4. **API Ekonomisi:** Gemini Free Tier (10 Key, Flash Lite modelleri) kullanılıyor. Rate-limit, key-rotation ve cache mekanizmaları mevcut.

## 📋 Proje Yapısı

```
/workspace
├── config.yaml              # Konfigürasyon dosyası
├── utils.py                 # Ortak yardımcı fonksiyonlar
├── requirements.txt         # Python bağımlılıkları
├── 01_geometry.py          # FAZ 1: Geometri ve Footprint Çıkarımı
├── 02_translate.py         # FAZ 2: LLM Çeviri Motoru (Yakında)
├── 03_inpaint.py           # FAZ 3: İnpainting (Yakında)
├── 04_render.py            # FAZ 4: Render ve Typesetting (Yakında)
├── output/
│   ├── debug/              # Debug görselleri
│   └── results/            # JSON sonuçları
└── data/
    ├── translation_cache.db # Çeviri önbelleği
    └── glossary.json       # Özel sözlük
```

## 🚀 Hızlı Başlangıç

### 1. Bağımlılıkları Kurun

```bash
pip install -r requirements.txt
```

### 2. FAZ 1'i Test Edin

```bash
# Tek bir görsel işleyin
python 01_geometry.py path/to/manga_page.png

# Veya tüm klasörü işleyin
python 01_geometry.py path/to/manga_pages/

# Sonuçları kaydetmeden test edin
python 01_geometry.py path/to/manga_page.png --no-save
```

### 3. Sonuçları İnceleyin

- **Debug Görseli:** `output/debug/{sayfa_adi}_detections.png`
  - Kırmızı kutular: minAreaRect (açılı dikdörtgen)
  - Yeşil çizgiler: Polygon sınırları
  - Mavi noktalar: Merkez noktaları
  - Etiketler: Block ID ve açı bilgisi

- **JSON Sonuçları:** `output/results/{sayfa_adi}_geometry.json`
  ```json
  {
    "text_blocks": [
      {
        "id": 0,
        "text": "Hello World",
        "confidence": 0.95,
        "polygon": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],
        "rect": {
          "center": [cx, cy],
          "size": [width, height],
          "angle": 15.5,
          "box": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        },
        "footprint": {
          "area": 1200,
          "aspect_ratio": 2.5,
          "pixels_per_char": 10.5
        }
      }
    ]
  }
  ```

## 📖 Fazlar

### ✅ FAZ 1: Geometri ve Ayak İzi Çıkarımı
- [x] PaddleOCR entegrasyonu
- [x] minAreaRect hesaplama
- [x] Polygon mask oluşturma
- [x] Footprint metrikleri (alan, açı, en-boy oranı)
- [x] Debug görselleştirme
- [x] JSON çıktı formatı

### ⏳ FAZ 2: LLM Orkestrasyonu ve Çeviri (Yakında)
- [ ] Gemini API entegrasyonu
- [ ] Çoklu API Key rotasyonu
- [ ] Glossary ve Translation Memory
- [ ] JSON schema doğrulama
- [ ] Rate-limit yönetimi

### ⏳ FAZ 3: Akıllı İnpainting (Yakında)
- [ ] LaMa / PatchMatch entegrasyonu
- [ ] Doku koruma
- [ ] Kenar interpolasyonu

### ⏳ FAZ 4: Render ve Typesetting (Yakında)
- [ ] Cairo / Skia render engine
- [ ] Footprint-eşleşmeli metin yerleştirme
- [ ] Dinamik font boyutu optimizasyonu
- [ ] Orijinal renk kopyalama

## 🔧 Konfigürasyon

`config.yaml` dosyasından özelleştirilebilir:

```yaml
ocr:
  provider: "paddleocr"  # paddleocr veya manga-ocr
  lang: "en"  # en, ja, ko
  use_angle_cls: true

geometry:
  min_text_area: 50
  merge_line_distance: 10

image:
  max_width: 2000
  max_height: 3000

output:
  debug_dir: "./output/debug"
  results_dir: "./output/results"
  rect_color: [255, 0, 0]  # Kırmızı (BGR)
```

## 🛠️ Sorun Giderme

### PaddleOCR Model İndirme Hatası
İlk çalıştırmada model dosyaları otomatik indirilir. İnternet bağlantınızı kontrol edin.

### Bellek Hatası (OOM)
Büyük görseller için `config.yaml` içindeki `max_width` ve `max_height` değerlerini düşürün.

### OCR Doğruluğu Düşük
- `det_db_thresh` ve `det_db_box_thresh` değerlerini ayarlayın
- Görüntüyü ön işlemeden geçirin (kontrast, parlaklık)
- `manga-ocr` alternatifini deneyin (Japonca için)

## 📝 Lisans

Bu proje eğitim ve araştırma amaçlıdır.

## 🤝 Katkıda Bulunma

Sorun bildirimleri ve önerileriniz için issue açabilirsiniz.
