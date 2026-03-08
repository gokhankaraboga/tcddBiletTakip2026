from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import argparse
import os
import time
import re
import json
from datetime import datetime

def _validate_config(cfg):
    required = ["NEREDEN", "NEREYE", "TARIH", "SAAT_BASLANGIC", "SAAT_BITIS", "MIN_KOLTUK"]
    for key in required:
        if key not in cfg or str(cfg[key]).strip() == "":
            raise ValueError(f"{key} bilgisi eksik!")
    return {
        "NEREDEN": str(cfg["NEREDEN"]).strip(),
        "NEREYE": str(cfg["NEREYE"]).strip(),
        "TARIH": str(cfg["TARIH"]).strip(),
        "SAAT_BASLANGIC": str(cfg["SAAT_BASLANGIC"]).strip(),
        "SAAT_BITIS": str(cfg["SAAT_BITIS"]).strip(),
        "MIN_KOLTUK": int(cfg["MIN_KOLTUK"]),
    }

def arama_konfigurasyonlarini_oku():
    """Öncelikle departureInfo.json, yoksa departureInfo.txt okur."""
    try:
        if os.path.exists("departureInfo.json"):
            with open("departureInfo.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            searches = data.get("searches", [])
            if not isinstance(searches, list) or not searches:
                raise ValueError("departureInfo.json içinde dolu bir 'searches' listesi olmalı.")
            return [_validate_config(cfg) for cfg in searches]

        # Legacy txt fallback (tek kombinasyon)
        legacy = {}
        with open("departureInfo.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    legacy[key.strip()] = value.strip()

        cfg = {
            "NEREDEN": legacy.get("NEREDEN", ""),
            "NEREYE": legacy.get("NEREYE", ""),
            "TARIH": legacy.get("TARIH", ""),
            "SAAT_BASLANGIC": legacy.get("SAAT BASLANGIC", ""),
            "SAAT_BITIS": legacy.get("SAAT BITIS", ""),
            "MIN_KOLTUK": int(legacy.get("KOLTUK SAYISI>", "0") or "0"),
        }
        return [_validate_config(cfg)]
    except Exception as e:
        print(f"Konfigürasyon okuma hatası: {str(e)}")
        return []

class TCDDBiletKontrol:
    CHROMIUM_PATH = os.environ.get("CHROMIUM_PATH", "/Applications/Chromium.app/Contents/MacOS/Chromium")
    CHROMEDRIVER_PATH = os.environ.get(
        "CHROMEDRIVER_PATH",
        os.path.join(os.path.dirname(__file__), "chromedriver")
    )

    def __init__(self):
        self.service = Service(self.CHROMEDRIVER_PATH)
        self.options = webdriver.ChromeOptions()
        self.options.binary_location = self.CHROMIUM_PATH
        self.options.add_argument('--headless=new')
        self.options.add_argument('--window-size=1920,1080')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--enable-javascript')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-setuid-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-dev-tools')
        self.options.add_argument('--disable-extensions')
        self.options.add_argument('--no-zygote')
        self.options.add_argument('--user-data-dir=/tmp/chrome-user-data')
        self.options.add_argument('--data-path=/tmp/chrome-data')
        self.options.add_argument('--disk-cache-dir=/tmp/chrome-cache')
        self.options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
        self.driver = None

    def tarayici_baslat(self):
        # Clean up temporary Chrome profile/cache directories between runs
        import shutil
        for item in ['/tmp/chrome-user-data', '/tmp/chrome-data', '/tmp/chrome-cache']:
            if os.path.exists(item):
                try:
                    shutil.rmtree(item, ignore_errors=True)
                except:
                    pass

        self.driver = webdriver.Chrome(service=self.service, options=self.options)
        self.sayfayi_sifirla()

    def sayfayi_sifirla(self):
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

    def sefer_bilgilerini_al(self):
        try:
            # Wait longer for page to load completely
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "time[title^='Gidiş']"))
            )

            # Give extra time for all elements to render
            time.sleep(3)

            allowed_types = {"BUSINESS", "LOCA", "EKONOMI"}
            sefer_saat_koltuk = {}

            vagon_butonlari = self.driver.find_elements(By.CSS_SELECTOR, "button[id*='-vagonType-']")

            for buton in vagon_butonlari:
                buton_text = (buton.get_attribute("innerText") or "").strip()
                tip_normalized = (buton_text
                    .upper()
                    .replace("İ", "I")
                    .replace("Ş", "S")
                    .replace("Ğ", "G")
                    .replace("Ü", "U")
                    .replace("Ö", "O")
                    .replace("Ç", "C")
                )

                if not any(allowed in tip_normalized for allowed in allowed_types):
                    continue

                koltuk_eslesme = re.search(r"\((\d+)\)", buton_text)
                koltuk_sayisi = int(koltuk_eslesme.group(1)) if koltuk_eslesme else 0

                if koltuk_sayisi <= 0:
                    continue

                saat_text = self.driver.execute_script(
                    """
                    let el = arguments[0];
                    for (let i = 0; i < 12 && el; i++, el = el.parentElement) {
                        const tm = el.querySelector("time[title^='Gidiş']");
                        if (tm) return tm.textContent.trim();
                    }
                    return "";
                    """,
                    buton,
                )

                match = re.search(r"\d{2}:\d{2}", saat_text or "")
                if not match:
                    continue

                saat = match.group(0)
                sefer_saat_koltuk[saat] = sefer_saat_koltuk.get(saat, 0) + koltuk_sayisi

            sefer_bilgileri = [
                {"saat": saat, "bos_koltuk": str(koltuk)}
                for saat, koltuk in sorted(sefer_saat_koltuk.items())
            ]

            return sefer_bilgileri

        except Exception as e:
            print(f"Sefer bilgileri alınırken hata oluştu: {str(e)}")
            return []

    def tarih_sec(self, tarih):
        try:
            gun_str, ay_str, yil_str = tarih.split(".")
            hedef_gun = int(gun_str)
            hedef_ay = int(ay_str)
            hedef_yil = int(yil_str)

            tarih_div = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".datePickerInput.departureDate"))
            )
            self.driver.execute_script("arguments[0].click();", tarih_div)
            
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".daterangepicker td"))
            )

            tarih_hucreleri = self.driver.find_elements(By.CSS_SELECTOR, ".daterangepicker td")
            for hucre in tarih_hucreleri:
                try:
                    hucre_class = hucre.get_attribute("class") or ""
                    if hucre.text.strip() != str(hedef_gun):
                        continue
                    if "disabled" in hucre_class or "off" in hucre_class:
                        continue

                    parent_table = hucre.find_element(By.XPATH, "./ancestor::table[1]")
                    ay_baslik = parent_table.find_element(
                        By.XPATH, "./thead//th[@class='month' or contains(@class,'month')]"
                    ).text.strip()
                    ay_baslik_norm = (ay_baslik
                        .lower()
                        .replace("ç", "c")
                        .replace("ğ", "g")
                        .replace("ı", "i")
                        .replace("ö", "o")
                        .replace("ş", "s")
                        .replace("ü", "u")
                    )

                    ay_haritasi = {
                        "ocak": 1, "subat": 2, "mart": 3, "nisan": 4, "mayis": 5, "haziran": 6,
                        "temmuz": 7, "agustos": 8, "eylul": 9, "ekim": 10, "kasim": 11, "aralik": 12
                    }
                    parcalar = ay_baslik_norm.split()
                    if len(parcalar) < 2:
                        continue
                    gorunen_ay = ay_haritasi.get(parcalar[0])
                    gorunen_yil = int(parcalar[1]) if parcalar[1].isdigit() else None
                    if gorunen_ay != hedef_ay or gorunen_yil != hedef_yil:
                        continue

                    if hucre.text.strip() == str(hedef_gun):
                        self.driver.execute_script("arguments[0].click();", hucre)
                        return True
                except:
                    continue

            raise Exception(f"{tarih} tarihi seçilemedi!")

        except Exception as e:
            print(f"Tarih seçiminde hata: {str(e)}")
            return False

    def bilet_kontrol(self):
        try:
            raise NotImplementedError("Bu metod artık bilet_kontrol_kombinasyon ile kullanılmalı.")
        except Exception as e:
            print(f"Bir hata oluştu: {str(e)}")
            return None

    def _sefer_sonuclarini_bekle(self, timeout=25):
        """
        Sefer arama sonrasında sonuçların yüklenmesini bekler.
        True: sefer elemanı bulundu
        False: timeout içinde sefer elemanı bulunamadı
        """
        end_time = time.time() + timeout
        while time.time() < end_time:
            bulunan_seferler = self.driver.find_elements(By.CSS_SELECTOR, "time[title^='Gidiş']")
            if bulunan_seferler:
                return True
            time.sleep(0.5)
        return False

    def seferleri_filtrele(self, sefer_bilgileri, saat_baslangic, saat_bitis, min_koltuk):
        bas = datetime.strptime(saat_baslangic, "%H:%M").time()
        bit = datetime.strptime(saat_bitis, "%H:%M").time()
        sonuc = []
        for sefer in sefer_bilgileri:
            try:
                saat = datetime.strptime(sefer["saat"], "%H:%M").time()
                koltuk = int(sefer["bos_koltuk"])
            except Exception:
                continue
            if bas <= saat <= bit and koltuk >= min_koltuk:
                sonuc.append(sefer)
        return sonuc

    def bilet_kontrol_kombinasyon(self, bilgiler):
        try:
            nereden = bilgiler["NEREDEN"]
            nereye = bilgiler["NEREYE"]
            tarih = bilgiler["TARIH"]
            saat_baslangic = bilgiler["SAAT_BASLANGIC"]
            saat_bitis = bilgiler["SAAT_BITIS"]
            min_koltuk = bilgiler["MIN_KOLTUK"]

            self.istasyon_sec("fromTrainInput", nereden)
            self.istasyon_sec("toTrainInput", nereye)
            
            if not self.tarih_sec(tarih):
                print(f"\nSefer yok! {nereden} - {nereye} için {tarih} tarihinde gidiş seferi bulunamadı.")
                return None

            sefer_ara_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, "searchSeferButton"))
            )
            sefer_bulundu = False
            for deneme in range(1, 4):
                self.driver.execute_script("arguments[0].click();", sefer_ara_button)
                if self._sefer_sonuclarini_bekle(timeout=25):
                    sefer_bulundu = True
                    break
                print(
                    f"Sefer sonucu henüz yüklenmedi ({deneme}/3): "
                    f"{nereden} - {nereye} | {tarih}"
                )
                try:
                    self.sayfayi_sifirla()
                    self.istasyon_sec("fromTrainInput", nereden)
                    self.istasyon_sec("toTrainInput", nereye)
                    if not self.tarih_sec(tarih):
                        return None
                    sefer_ara_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "searchSeferButton"))
                    )
                except Exception:
                    pass

            if not sefer_bulundu:
                print(f"Sefer yok! {nereden} - {nereye} | {tarih}")
                return {"status": "no_trip"}

            sefer_bilgileri = self.sefer_bilgilerini_al()
            uygun_seferler = self.seferleri_filtrele(sefer_bilgileri, saat_baslangic, saat_bitis, min_koltuk)

            if uygun_seferler:
                return {
                    "status": "found",
                    "sefer_bilgileri": sefer_bilgileri,
                    "uygun_seferler": uygun_seferler,
                    "nereden": nereden,
                    "nereye": nereye,
                    "tarih": tarih,
                    "saat_baslangic": saat_baslangic,
                    "saat_bitis": saat_bitis,
                    "min_koltuk": min_koltuk,
                }
            else:
                print(
                    f"Koltuk yok! {nereden} - {nereye} | {tarih} "
                    f"({saat_baslangic}-{saat_bitis}, >={min_koltuk})"
                )
                return {"status": "no_seat"}

        except Exception as e:
            print(f"Bir hata oluştu: {str(e)}")
            return {"status": "error"}

    def kapat(self):
        if self.driver:
            self.driver.quit()

def run_checks(kombinasyonlar=None, send_notification=True):
    if kombinasyonlar is None:
        kombinasyonlar = arama_konfigurasyonlarini_oku()
    else:
        kombinasyonlar = [_validate_config(k) for k in kombinasyonlar]

    if not kombinasyonlar:
        return {
            "ok": False,
            "checked": 0,
            "matched": False,
            "message": "Konfigürasyon bulunamadı veya geçersiz."
        }

    kontrol = TCDDBiletKontrol()
    checked = 0
    try:
        kontrol.tarayici_baslat()
        for i, kombinasyon in enumerate(kombinasyonlar, start=1):
            checked += 1
            print(
                f"\n[{i}/{len(kombinasyonlar)}] Kontrol: "
                f"{kombinasyon['NEREDEN']} -> {kombinasyon['NEREYE']} | {kombinasyon['TARIH']}"
            )
            kontrol.sayfayi_sifirla()
            sonuc = kontrol.bilet_kontrol_kombinasyon(kombinasyon)
            if sonuc and sonuc.get("status") == "found":
                if send_notification:
                    from sendTelegram import send_telegram_message
                    send_telegram_message(
                        sonuc["uygun_seferler"],
                        sonuc["nereden"],
                        sonuc["nereye"],
                        sonuc["tarih"],
                        sonuc["saat_baslangic"],
                        sonuc["saat_bitis"],
                        sonuc["min_koltuk"],
                    )
                return {
                    "ok": True,
                    "checked": checked,
                    "matched": True,
                    "result": sonuc
                }

        print("\nHiçbir kombinasyonda uygun koltuk bulunamadı.")
        return {
            "ok": True,
            "checked": checked,
            "matched": False
        }
    finally:
        kontrol.kapat()


def _parse_bool_text(value):
    return str(value).strip().lower() == "true"


def _secili_kombinasyonlari_hazirla(combo_index):
    kombinasyonlar = arama_konfigurasyonlarini_oku()
    if combo_index is None:
        return kombinasyonlar
    if combo_index < 0 or combo_index >= len(kombinasyonlar):
        raise ValueError(
            f"Geçersiz COMBO_INDEX: {combo_index}. "
            f"Geçerli aralık: 0..{max(len(kombinasyonlar)-1, 0)}"
        )
    return [kombinasyonlar[combo_index]]


def _argumanlari_oku():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--combo-index",
        type=int,
        default=None,
        help="Sadece belirli bir kombinasyonu çalıştırır (0 tabanlı indeks).",
    )
    parser.add_argument(
        "--send-telegram",
        choices=["true", "false"],
        default=None,
        help="Telegram gönderimini zorlar (true/false).",
    )
    return parser.parse_args()

def main():
    args = _argumanlari_oku()

    if args.send_telegram is not None:
        send_notification = _parse_bool_text(args.send_telegram)
    else:
        send_notification = _parse_bool_text(os.getenv("SEND_TELEGRAM", "true"))

    if args.combo_index is not None:
        combo_index = args.combo_index
    else:
        combo_env = os.getenv("COMBO_INDEX")
        combo_index = int(combo_env) if combo_env not in (None, "") else None

    kombinasyonlar = _secili_kombinasyonlari_hazirla(combo_index)
    if combo_index is not None:
        print(f"Sadece COMBO_INDEX={combo_index} çalıştırılıyor.")

    result = run_checks(kombinasyonlar=kombinasyonlar, send_notification=send_notification)
    if not result.get("ok"):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
