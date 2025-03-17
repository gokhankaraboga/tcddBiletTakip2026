from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def departureInfo_oku():
    """departureInfo.txt dosyasından bilgileri okur"""
    try:
        bilgiler = {}
        with open('departureInfo.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    bilgiler[key.strip()] = value.strip()
        
        # Gerekli bilgilerin kontrolü
        gerekli_bilgiler = ['NEREDEN', 'NEREYE', 'TARIH']
        for bilgi in gerekli_bilgiler:
            if not bilgiler.get(bilgi):
                raise ValueError(f"{bilgi} bilgisi eksik!")
        
        return bilgiler
    except Exception as e:
        print(f"Dosya okuma hatası: {str(e)}")
        return None

class TCDDBiletKontrol:
    def __init__(self):
        self.service = Service(ChromeDriverManager().install())
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.driver = None

    def tarayici_baslat(self):
        self.driver = webdriver.Chrome(service=self.service, options=self.options)
        self.driver.maximize_window()
        self.driver.get("https://ebilet.tcddtasimacilik.gov.tr/view/eybis/tnmGenel/tcddWebContent.jsf")
        
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "fromTrainInput"))
        )

    def istasyon_sec(self, input_id, istasyon_adi):
        try:
            istasyon_input = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, input_id))
            )
            self.driver.execute_script("arguments[0].click();", istasyon_input)

            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.dropdown-item.station"))
            )

            istasyon_butonlari = self.driver.find_elements(By.CSS_SELECTOR, "button.dropdown-item.station")

            for buton in istasyon_butonlari:
                istasyon_text = buton.find_element(By.CLASS_NAME, "textLocation").text
                if istasyon_adi in istasyon_text:
                    self.driver.execute_script("arguments[0].click();", buton)
                    return True

            raise Exception(f"'{istasyon_adi}' istasyonu bulunamadı!")

        except Exception as e:
            print(f"İstasyon seçiminde hata: {str(e)}")
            raise

    def sefer_bilgilerini_kaydet(self, sefer_bilgileri, nereden, nereye, tarih):
        """Sefer bilgilerini dosyaya kaydeder"""
        try:
            with open('departureTimes.txt', 'w', encoding='utf-8') as f:
                f.write(f"{nereden} - {nereye} için {tarih} tarihinde gidiş seferleri:\n")
                f.write("\nSaat   Boş Koltuk\n")
                f.write("-" * 20 + "\n")
                for sefer in sefer_bilgileri:
                    f.write(f"{sefer['saat']}    {sefer['bos_koltuk']}\n")
            print("\nSefer bilgileri departureTimes.txt dosyasına kaydedildi.")
        except Exception as e:
            print(f"Dosyaya yazma hatası: {str(e)}")

    def sefer_bilgilerini_al(self):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "time[title^='Gidiş']"))
            )
            
            sefer_saatleri = self.driver.find_elements(By.CSS_SELECTOR, "time[title^='Gidiş']")
            bos_koltuklar = self.driver.find_elements(By.CLASS_NAME, "emptySeat")
            
            sefer_bilgileri = []
            for saat, koltuk in zip(sefer_saatleri, bos_koltuklar):
                sefer = {
                    'saat': saat.text.strip(),
                    'bos_koltuk': koltuk.text.strip('()')
                }
                sefer_bilgileri.append(sefer)
            
            return sefer_bilgileri

        except Exception as e:
            print(f"Sefer bilgileri alınırken hata oluştu: {str(e)}")
            return []

    def tarih_sec(self, tarih):
        try:
            tarih_div = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "datePickerInput.departureDate"))
            )
            self.driver.execute_script("arguments[0].click();", tarih_div)

            gun = tarih.split('.')[0]
            
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "td[data-v-6e3c8fef]"))
            )

            tarih_hucreleri = self.driver.find_elements(By.CSS_SELECTOR, "td[data-v-6e3c8fef]")
            for hucre in tarih_hucreleri:
                try:
                    span = hucre.find_element(By.TAG_NAME, "span")
                    if span.text == gun and "disabled" not in hucre.get_attribute("class"):
                        self.driver.execute_script("arguments[0].click();", span)
                        return True
                except:
                    continue

            raise Exception(f"{tarih} tarihi seçilemedi!")

        except Exception as e:
            print(f"Tarih seçiminde hata: {str(e)}")
            raise

    def bilet_kontrol(self):
        try:
            bilgiler = departureInfo_oku()
            if not bilgiler:
                return False

            nereden = bilgiler['NEREDEN']
            nereye = bilgiler['NEREYE']
            tarih = bilgiler['TARIH']

            self.istasyon_sec("fromTrainInput", nereden)
            self.istasyon_sec("toTrainInput", nereye)
            
            self.tarih_sec(tarih)

            sefer_ara_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, "searchSeferButton"))
            )
            self.driver.execute_script("arguments[0].click();", sefer_ara_button)

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "time[title^='Gidiş']"))
            )

            sefer_bilgileri = self.sefer_bilgilerini_al()
            
            if sefer_bilgileri:
                self.sefer_bilgilerini_kaydet(sefer_bilgileri, nereden, nereye, tarih)
                return True
            else:
                print(f"\nSefer bulunamadı! {nereden} - {nereye} için {tarih} tarihinde gidiş seferi yok.")
                return False

        except Exception as e:
            print(f"Bir hata oluştu: {str(e)}")
            return False

    def kapat(self):
        if self.driver:
            self.driver.quit()

def main():
    kontrol = TCDDBiletKontrol()
    try:
        kontrol.tarayici_baslat()
        if kontrol.bilet_kontrol():
            # Sefer bilgileri bulundu ve kaydedildi, şimdi Telegram mesajı gönder
            from sendTelegram import send_telegram_message
            send_telegram_message()
    finally:
        kontrol.kapat()

if __name__ == "__main__":
    main()