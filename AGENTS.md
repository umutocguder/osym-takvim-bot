# ÖSYM Takvim Bot — AI talimatları

Genel bağlam: `/Users/umut/ai-context/README.md` ve `/Users/umut/ai-context/projeler/osym-takvim-bot.md`.

- Kod, log ve hata mesajları İngilizce; kodda açıklayıcı yorum yok.
- Yalnız Python standart kütüphanesi kullanılır; indirme `/usr/bin/curl` ile (python.org Python'unda SSL sertifikası yok).
- Kullanıcıya görünen olay metinleri `config.json` → `labels` içinde Türkçe tutulur.
- Takvime yazmadan önce `python3 -m osym_bot --dry-run` ile kontrol et.
- ÖSYM sayfası değişirse önce `tests/fixtures/` altına yeni tarihli kesit ekle, sonra ayrıştırıcıyı düzelt.
