import requests
from datetime import datetime

class TelegramBot:
    def __init__(self):
        self.BOT_TOKEN = "xxx"
        self.chat_id = xxx

    def read_info(self):
        """departureInfo.txt dosyasından bilgileri okur"""
        with open('departureInfo.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            info = {}
            for line in lines:
                if 'SAAT BASLANGIC=' in line:
                    info['start'] = line.split('=')[1].strip()
                elif 'SAAT BITIS=' in line:
                    info['end'] = line.split('=')[1].strip()
                elif 'KOLTUK SAYISI>=' in line:
                    info['min_seats'] = int(line.split('>=')[1].strip())
            return info

    def filter_times(self, content, start_time, end_time, min_seats):
        """Sefer bilgilerini saat aralığına ve koltuk sayısına göre filtreler"""
        lines = content.split('\n')
        header = [line for line in lines[:4]]  # Başlık satırlarını al
        
        filtered_times = []
        for line in lines[4:]:  # Başlık sonrası satırları kontrol et
            if line.strip() and line[0].isdigit():
                parts = line.split()
                if len(parts) >= 2:
                    time = datetime.strptime(parts[0], '%H:%M').time()
                    seats = int(parts[1])
                    if (datetime.strptime(start_time, '%H:%M').time() <= time <= 
                        datetime.strptime(end_time, '%H:%M').time() and 
                        seats >= min_seats):
                        filtered_times.append(line.strip())

        return '\n'.join(header + filtered_times) if filtered_times else None

    def send_message(self):
        # Bilgileri oku
        info = self.read_info()
        with open('departureTimes.txt', 'r', encoding='utf-8') as f:
            content = f.read()

        # Sefer bilgilerini filtrele
        filtered_content = self.filter_times(
            content, 
            info['start'], 
            info['end'], 
            info['min_seats']
        )

        # Eğer kriterlere uyan sefer yoksa mesaj gönderme
        if not filtered_content:
            print(f"Belirtilen kriterlere ({info['start']}-{info['end']}, >={info['min_seats']} koltuk) uygun sefer bulunamadı!")
            return

        # Mesajı gönder
        url = f"https://api.telegram.org/bot{self.BOT_TOKEN}/sendMessage"
        message = f"TCDD Sefer Bilgileri - {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n{filtered_content}"
        
        response = requests.post(url, data={
            "chat_id": self.chat_id,
            "text": message
        })
        
        print("Uygun sefer bulundu ve mesaj gönderildi!" if response.status_code == 200 else "Mesaj gönderilemedi!")

def send_telegram_message():
    TelegramBot().send_message()

if __name__ == "__main__":
    send_telegram_message() 