import requests
import os
from datetime import datetime
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

        filtered_lines = [f"{s['saat']}    {s['bos_koltuk']}" for s in uygun_seferler]
        body = "\n".join(filtered_lines)
        filtered_content = (
            f"{nereden} - {nereye} için {tarih} tarihinde gidiş seferleri:\n\n"
            f"Kriter: {saat_baslangic}-{saat_bitis}, en az {min_koltuk} koltuk\n\n"
            "Saat   Boş Koltuk\n"
            "--------------------\n"
            f"{body}"
        )

        # Mesajı gönder
        url = f"https://api.telegram.org/bot{self.BOT_TOKEN}/sendMessage"
        message = f"TCDD Sefer Bilgileri - {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n{filtered_content}"
        
        response = requests.post(url, data={
            "chat_id": self.chat_id,
            "text": message
        })
        
        print("Uygun sefer bulundu ve mesaj gönderildi!" if response.status_code == 200 else "Mesaj gönderilemedi!")

def send_telegram_message(uygun_seferler, nereden, nereye, tarih, saat_baslangic, saat_bitis, min_koltuk):
    TelegramBot().send_message(uygun_seferler, nereden, nereye, tarih, saat_baslangic, saat_bitis, min_koltuk)

if __name__ == "__main__":
    print("Bu dosya doğrudan çalıştırılmak yerine main.py içinden çağrılmalıdır.")
