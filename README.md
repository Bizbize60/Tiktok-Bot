
# 📺 TikTok Live Viewer Botu(Eğitim Amaçlıdır,Education Purposed)

Bu proje, Tor ağı üzerinden IP değiştirerek, TikTok canlı yayınlarına giriş yapan ve captcha çözen çoklu hesap destekli bir otomasyon botudur.

---

## 🚀 Özellikler

- Tor Proxy kullanarak her bağlantı öncesi yeni IP alır.
- undetected-chromedriver ile Selenium tespiti azaltılır.
- tiktok-captcha-solver entegrasyonu ile captcha çözme.
- Fake Keyboard Activity ile insan aktivitesi simüle edilir.
- Multi-thread desteğiyle çoklu hesap aynı anda yönetilir.
- Retry sistemi ile hatalı girişlerde otomatik tekrar denenir.
- Captcha slider hareketi insana benzeyen şekilde yapılır.

---

## 🛠 Kurulum

1. Python 3.8+ kurulu olduğundan emin ol.
2. Gerekli paketleri yüklemek için:

```bash
pip install -r requirements.txt
```

3. Şu bilgileri kendi ortamına göre düzenle:
    - `TOR_PROXY`
    - `api_key`
    - `yayın linki`
    - `email` ve `password` listesi

4. Uygulamayı çalıştır:

```bash
python main.py
```

---

## 💡 Gereksinimler

- Tor servisi aktif çalışmalı (127.0.0.1:9050 varsayılan).
- tiktok-captcha-solver için API key gerekli.
- Google Chrome ve ChromeDriver sürüm uyumlu olmalı.
- Doğrulama kodu için webmail hesabına erişim olmalı.

---

## 📚 Proje Yapısı

| Dosya | Açıklama |
|:---|:---|
| main.py | Ana uygulama scripti |
| requirements.txt | Python kütüphaneleri listesi |

---

## 📚 Kullanılan Teknolojiler

- Selenium
- undetected-chromedriver
- Tor (stem modülü ile IP kontrol)
- OpenCV
- pyautogui
- requests
- pynput
- selenium-stealth
- threading

---

## ⚠️ Dikkat Edilmesi Gerekenler

- Proxy hataları botun çalışmasını durdurabilir.
- API limiti dolarsa captcha çözülemez.
- XPath yapıları TikTok güncellemelerinde değişebilir.

---

## 📜 requirements.txt

```text
tiktok-captcha-solver
selenium
opencv-python
numpy
pyautogui
requests
stem
pynput
undetected-chromedriver
selenium-stealth
```

---

## 👑 Hazırlayan

**Dost Canlısı Bir Yazılımcı** ✨

„ Bu proje insan gibi görünerek TikTok yayınlarına otomatik girme çalışması için geliştirilmiştir. Yardım gerekirse her zaman buradayım! 🚀
