from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from stem.control import Controller
from stem import Signal
import time
import threading

# Tor Proxy Ayarı
TOR_PROXY = "socks5://127.0.0.1:9050"

def change_tor_ip():
    
    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password="Tokatlireis60")  # Şifreni buraya yaz
            controller.signal(Signal.NEWNYM)  # Yeni kimlik talep et
            print("Yeni Tor IP alındı!")
            time.sleep(5)  
    except Exception as e:
        print(f"Tor IP değiştirilemedi! Hata: {e}")

def create_browser(profile_dir):
    
    options = Options()
    options.add_argument(f"--user-data-dir={profile_dir}")  
    options.add_argument("--disable-blink-features=AutomationControlled")  
    options.add_argument(f"--proxy-server={TOR_PROXY}")  
    options.add_argument("--mute-audio")  
    options.add_argument("--no-sand-box")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--mute-audio")
    options.add_argument("--disable-gpu")
    options.add_argument("--headless=new")


    try:
        return webdriver.Chrome(options=options)
    except Exception as e:
        print(f"Tarayıcı başlatılamadı! Hata: {e}")
        return None

def watch_live(profile):
    
    print(f"{profile} için yeni IP alınıyor")
    change_tor_ip()  # ip değiştir

    browser = create_browser(profile)  

    if browser:
        try:
            browser.get("https://www.tiktok.com/@_yelda1/live")  # Canlı yayın URL'sine git
            print(f"{profile} yayına bağlandı! ✅")
            
            while True:
                time.sleep(60)  
        except Exception as e:
            print(f"{profile} yayına bağlanamadı! Hata: {e}")
    else:
        print(f"{profile} için tarayıcı açılamadı! 🚫")
profiles = []
# Örnek Profiller
for i in range(100):
    profiles.append(f"profile{i}")


# Her profil için ayrı thread başlat
threads = []
for profile in profiles:
    t = threading.Thread(target=watch_live, args=(profile,))
    t.start()
    threads.append(t)

# Tüm thread'lerin bitmesini bekle (sonsuz döngüde olduğu için kapanmayacak)
for t in threads:
    t.join()
