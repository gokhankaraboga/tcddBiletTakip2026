import requests
import os
from dotenv import load_dotenv

load_dotenv()

class TelegramBot:
    def __init__(self):
        self.BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    def send_message(self, uygun_seferler, nereden, nereye, tarih, saat_baslangic, saat_bitis, min_koltuk):
        if not self.BOT_TOKEN or not self.chat_id:
            print("Telegram ayarları eksik. TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID ortam değişkenlerini ayarlayın.")
            return

        if not uygun_seferler:
            return

        filtered_lines = []
        for s in uygun_seferler:
            saat_metni = s.get("segment_saatleri") or s.get("saat", "")
            filtered_lines.append(f"{saat_metni}: {s['bos_koltuk']}")
        body = "\n".join(filtered_lines)

        # Mesajı gönder
        url = f"https://api.telegram.org/bot{self.BOT_TOKEN}/sendMessage"
        message = (
            f"{nereden} -> {nereye} | {tarih}\n"
            f"Uygun:\n{body}"
        )
        
        response = requests.post(url, data={
            "chat_id": self.chat_id,
            "text": message
        })
        
        print("Uygun sefer bulundu ve mesaj gönderildi!" if response.status_code == 200 else "Mesaj gönderilemedi!")

def send_telegram_message(uygun_seferler, nereden, nereye, tarih, saat_baslangic, saat_bitis, min_koltuk):
    TelegramBot().send_message(uygun_seferler, nereden, nereye, tarih, saat_baslangic, saat_bitis, min_koltuk)

if __name__ == "__main__":
    print("Bu dosya doğrudan çalıştırılmak yerine main.py içinden çağrılmalıdır.")
