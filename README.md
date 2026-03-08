# TCDD Bilet Takip Programı

Bu program, TCDD'nin e-bilet sistemindeki tren seferlerini otomatik olarak kontrol eden ve belirli kriterlere uyan seferleri Telegram üzerinden bildiren bir otomasyon aracıdır.

## Özellikler

- Birden fazla arama kombinasyonunu (`departureInfo.json`) üstten alta sırayla kontrol eder
- İlk uygun sonucu bulduğunda Telegram bildirimi gönderir ve döngüyü durdurur
- Saat aralığına ve minimum koltuk sayısına göre filtreleme yapar
- Sadece `BUSINESS`, `LOCA`, `EKONOMİ` koltuk tiplerini dikkate alır
- `TEKERLEKLİ SANDALYE` koltuk tipini hariç tutar
- Chromium'u headless modda çalıştırır

## Gereksinimler

- Python 3.x
- Selenium
- requests
- python-dotenv
- Yerel `chromedriver` binary'si (proje kökünde)
- Chromium (varsayılan yol: `/Applications/Chromium.app/Contents/MacOS/Chromium`)

## Kurulum

1. Gerekli Python paketlerini yükleyin:
```bash
pip install -r requirements.txt
```

2. Telegram bilgilerini `.env` dosyasına girin:
```env
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
TELEGRAM_CHAT_ID=YOUR_CHAT_ID_HERE
```

## Kullanım

### Arama Kombinasyonlarını Ayarlama

`departureInfo.json` dosyasını aşağıdaki formatta düzenleyin:

```json
{
  "searches": [
    {
      "NEREDEN": "KARAMAN , KARAMAN",
      "NEREYE": "İSTANBUL(HALKALI) , İSTANBUL",
      "TARIH": "24.03.2026",
      "SAAT_BASLANGIC": "06:00",
      "SAAT_BITIS": "18:00",
      "MIN_KOLTUK": 1
    },
    {
      "NEREDEN": "KARAMAN , KARAMAN",
      "NEREYE": "İSTANBUL(HALKALI) , İSTANBUL",
      "TARIH": "25.03.2026",
      "SAAT_BASLANGIC": "06:00",
      "SAAT_BITIS": "18:00",
      "MIN_KOLTUK": 1
    }
  ]
}
```

Not: `departureInfo.txt` tek kombinasyon için geriye dönük uyumluluk amacıyla hala desteklenir.

### Programı Çalıştırma

```bash
.venv/bin/python main.py
```

### Docker ile Çalıştırma

1. Image build:
```bash
docker build -t tcdd-bilet-takip:local .
```

2. Container çalıştırma:
```bash
docker run --rm \
  --env-file .env \
  -e SEND_TELEGRAM=false \
  -v "$(pwd)/departureInfo.json:/app/departureInfo.json:ro" \
  tcdd-bilet-takip:local
```

Notlar:
- Container içinde Chromium + Chromedriver hazır gelir.
- Kod `main.py` ile direkt çalışır.
- Bu image yapısı GitHub Actions tarafında da tekrar kullanılabilir.

### Gizli Konfigürasyon (GitHub Actions)

`departureInfo.json` dosyasını public repoda tutmak istemiyorsanız, aşağıdaki secret'ı tanımlayın:

- `DEPARTURE_INFO_JSON`: `departureInfo.json` içeriğinin tamamı (tek satır JSON metni)

Workflow bu secret'tan kombinasyonları okur. Örnek değer için `departureInfo.example.json` kullanılabilir.

## Dosya Yapısı

- `main.py`: Ana program dosyası, TCDD web sitesini kontrol eder ve kombinasyon döngüsünü yönetir
- `sendTelegram.py`: Telegram mesaj gönderme işlemlerini yönetir
- `departureInfo.json`: Birden fazla arama kombinasyonu
- `.env`: Telegram kimlik bilgileri (git'e eklenmemeli)
- `runProject.ps1`: PowerShell otomatik çalıştırma scripti

## Çalışma Mantığı

1. `searches` listesindeki kombinasyonlar sırayla çalıştırılır
2. Her kombinasyonda sefer var/yok kontrolü yapılır
3. Sefer varsa sadece `BUSINESS/LOCA/EKONOMİ` tiplerindeki boş koltuklar toplanır
4. Saat aralığı + minimum koltuk filtresi uygulanır
5. İlk uygun sonuçta Telegram mesajı gönderilir ve döngü sonlanır
6. Hiçbir kombinasyonda uygun sonuç yoksa bildirim gönderilmez
