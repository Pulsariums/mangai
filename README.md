# Manga Translator - Rust + Tauri v2

Tamamen Rust ile yazılmış, mobil ve masaüstü platformlarında çalışan manga/manhwa çeviri uygulaması.

## Özellikler

- **Cross-Platform**: Tek kod tabanı ile Windows, macOS, Linux, iOS ve Android desteği
- **Minimal Boyut**: Optimize edilmiş release profili ile minimum indirme boyutu
- **Modern UI**: Mor temalı, koyu/açık mod destekli, blur içermeyen düz tasarım
- **Yüksek Performans**: Rust'ın bellek güvenliği ve hızı

## Teknolojiler

- **Backend**: Rust
- **Frontend**: Vanilla JS + CSS (framework'süz, minimal)
- **UI Framework**: Tauri v2
- **Resim İşleme**: `image` crate
- **HTTP Client**: `reqwest`
- **Veritabanı**: `rusqlite`

## Kurulum

```bash
# Rust kurulu olmalı
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Node.js (opsiyonel, web geliştirme için)
npm install -g tauri-cli

# Projeyi derle
cargo build --release
```

## Çalıştırma

```bash
# Development modu
cargo tauri dev

# Release build
cargo tauri build
```

## Proje Yapısı

```
├── Cargo.toml          # Rust bağımlılıkları
├── src-tauri/
│   ├── src/
│   │   ├── lib.rs      # Tauri komutları ve mantık
│   │   └── main.rs     # Uygulama entry point
│   ├── build.rs        # Build script
│   ├── tauri.conf.json # Tauri konfigürasyonu
│   └── icons/          # Uygulama ikonları
└── src/frontend/
    ├── index.html      # Ana HTML
    ├── styles.css      # CSS (mor tema, dark/light mode)
    └── app.js          # Frontend mantığı
```

## Tasarım Prensipleri

- **Mor (#7C3AED)**: Ana vurgu rengi
- **İnce Borderlar**: 1px solid çizgiler
- **Düz Renkler**: Blur/gradientsiz
- **Hızlı Animasyonlar**: 150-200ms cubic-bezier
- **Apple-esintili**: Switch'ler ve butonlar iOS tarzı

## Lisans

MIT
