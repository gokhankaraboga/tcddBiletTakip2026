# TCDD Bilet Takip Programı

Bu program, TCDD'nin e-bilet sistemindeki tren seferlerini otomatik olarak kontrol eden ve belirli kriterlere uyan seferleri Telegram üzerinden bildiren bir otomasyon aracıdır.

## Özellikler

- Belirtilen güzergah için tren seferlerini otomatik kontrol
- Belirlenen saat aralığında sefer filtreleme
- Minimum boş koltuk sayısına göre filtreleme
- Telegram üzerinden anlık bildirim
- Otomatik periyodik kontrol (PowerShell script ile)

## Gereksinimler

- Python 3.x
- Selenium
- webdriver-manager
- requests

## Kurulum

1. Gerekli Python paketlerini yükleyin:
```bash
pip install selenium webdriver-manager requests
```

2. Telegram bot token'ınızı ve chat ID'nizi `sendTelegram.py` dosyasında güncelleyin.

## Kullanım

### Sefer Bilgilerini Ayarlama

`departureInfo.txt` dosyasını aşağıdaki formatta düzenleyin: 
NEREDEN=İSTANBUL(BOSTANCI) , İSTANBUL
NEREYE=ESKİŞEHİR
TARIH=29.03.2025
SAAT BASLANGIC=06:00
SAAT BITIS=13:00
KOLTUK SAYISI>=2

### Programı Çalıştırma

PowerShell üzerinden otomatik kontrol için:
1. PowerShell'i yönetici olarak açın
2. Proje dizinine gidin
3. Aşağıdaki komutu çalıştırın:
```powershell
.\runProject.ps1
```

## Dosya Yapısı

- `main.py`: Ana program dosyası, TCDD web sitesini kontrol eder
- `sendTelegram.py`: Telegram mesaj gönderme işlemlerini yönetir
- `departureInfo.txt`: Sefer arama kriterleri
- `departureTimes.txt`: Bulunan seferlerin kaydedildiği dosya
- `runProject.ps1`: Otomatik kontrol için PowerShell script

tcddBiletTakip/
│
├── main.py # Ana program dosyası
├── sendTelegram.py # Telegram mesaj gönderme modülü
├── runProject.ps1 # PowerShell otomatik çalıştırma scripti
│
├── departureInfo.txt # Sefer arama kriterleri
├── departureTimes.txt # Bulunan seferlerin kayıtları
│
└── README.md # Proje dokümantasyonu

## Çalışma Mantığı

1. Program her dakika çalışır
2. TCDD web sitesinden sefer bilgilerini çeker
3. Bulunan seferleri `departureTimes.txt` dosyasına kaydeder
4. Belirtilen kriterlere (saat aralığı ve koltuk sayısı) uyan seferler varsa:
   - Telegram üzerinden bildirim gönderir
5. Kriterlere uyan sefer yoksa:
   - Bildirim göndermez ve bir sonraki kontrolü bekler
