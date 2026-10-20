# ÖSYM Takvim Bot

ÖSYM'nin [sınav takvimi sayfasını](https://www.osym.gov.tr/Sayfa/SinavTakvimi) her ayın 1'inde okur,
seçili sınavların **başvuru**, **geç başvuru** ve **sınav** tarihlerini macOS Takvim üzerinden
Google Takvim'deki **"ÖSYM Sınavları"** takvimine ekler.

## Takip edilen sınavlar

| Sınav | Kural |
|---|---|
| ALES | Tüm oturumlar |
| KPSS | Yalnız **Lisans** (GY-GK, Alan Bilgisi). Ön Lisans, Ortaöğretim, DHBT hariç |
| YÖKDİL | Yalnız kâğıt sınav. **e-YÖKDİL hariç** |
| YDS | Yalnız kâğıt sınav. **e-YDS hariç** |

Liste `config.json` içindeki `exams` alanından değiştirilir.

## Ne eklenir

| Olay | Biçim | Hatırlatıcı |
|---|---|---|
| `2026-ALES/3 · Başvuru` | Tüm gün, başvuru başlangıcından bitişine | İlk gün 09:00 + son gün 09:00 |
| `2026-ALES/3 · Geç Başvuru` | Tüm gün | İlk gün 09:00 (+ çok günlüyse son gün) |
| `2026-ALES/3 · Sınav` | Saat varsa 3 saatlik olay, yoksa tüm gün | 1 hafta önce, 1 gün önce, (saatliyse) 2 saat önce |

- KPSS Lisans oturumlarının başvurusu ortak olduğu için tek "2026-KPSS Lisans · Başvuru" olayı açılır.
- Yalnız **bugünden sonraki** tarihler eklenir; geçmiş tarihler eklenmez.
- Her olayın notunun ilk satırında `osym-bot:<anahtar>#<parmak izi>` işareti vardır. Bot bununla
  aynı olayı tekrar eklemez; ÖSYM bir tarihi değiştirirse eski olayı silip yenisini ekler.
- Yeni yılın takvimi yayımlandığında aynı sayfadan otomatik alınır.

## Nasıl çalışır

```
launchd (her ayın 1'i 10:00)
  └─ python3 -m osym_bot
       ├─ scraper.py        curl ile sayfayı indirir, tabloyu ayrıştırır
       ├─ events.py         filtre + takvim olaylarını üretir
       └─ apple_calendar.py osascript ile Takvim'e yazar (Google'a senkronlanır)
```

Mac uykudaysa launchd işi uyanınca çalıştırır. Hata olursa ve yeni olay eklenirse macOS bildirimi gelir.
Günlük: `~/Library/Logs/osym-takvim-bot.log`.

Ek Python paketi gerekmez (yalnız standart kütüphane).

## Kurulum

1. Google Takvim'de **ÖSYM Sınavları** adlı takvimi aç (Mac Takvim'de görünmesini bekle).
2. Kur ve ilk çalıştırmayı hemen yap:

```bash
./scripts/install.sh --run-now
```

İlk çalıştırmada macOS "python3, Takvim'i denetlemek istiyor" diye sorar → **İzin Ver**.

## Komutlar

```bash
python3 -m osym_bot --dry-run          # takvime dokunmadan ne ekleneceğini gösterir
python3 -m osym_bot                    # senkronu elle çalıştırır
python3 -m unittest -v                 # testler
./scripts/uninstall.sh                 # zamanlanmış işi kaldırır
tail -f ~/Library/Logs/osym-takvim-bot.log
```

## Dikkat

- ÖSYM sayfa yapısını değiştirirse bot "No calendar rows found" hatası verir ve bildirim gönderir;
  `osym_bot/scraper.py` güncellenmelidir. Test verisi: `tests/fixtures/sinav_takvimi_2026.html` (20.10.2026).
- Takvim adı benzersiz olmalıdır (Mac Takvim'de aynı adda iki takvim varsa bot yazmaz).
