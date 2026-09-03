import os
import requests
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

BOT_TOKEN = "8656415127:AAHkqmZdW0b2NGzqRb-iRqhCkUNG4SwAN1w"
CHAT_ID = "8210045794"

# Bildirilen skor ve canlı durum hafızası
bildirilen_maclar = set()

class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Garanti Gol Radari Aktif!")

    def log_message(self, format, *args):
        return

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyServer)
    server.serve_forever()

def telegram_bildir(mesaj):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, data=payload, timeout=10)
        print(f"Telegram Gönderim Durumu: {res.status_code}")
    except Exception as e:
        print("Telegram hatası:", e)

def mackolik_garanti_tara():
    global bildirilen_maclar
    url = "https://m.mackolik.com/api/livematches"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://m.mackolik.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Maçkolik Sunucu Hatası: {response.status_code}")
            return

        data = response.json()
        matches = data.get("data", [])
        
        # Sadece o an oynanan canlı maçları al
        canli_maclar = [m for m in matches if m.get("status", {}).get("isLive", False)]
        print(f"🟢 Canlıdaki Aktif Maç Sayısı: {len(canli_maclar)}")

        for mac in canli_maclar:
            mac_id = mac.get("id")
            ev = mac.get("homeTeam", {}).get("name", "Ev")
            dep = mac.get("awayTeam", {}).get("name", "Dep")
            skor_ev = mac.get("score", {}).get("home", 0)
            skor_dep = mac.get("score", {}).get("away", 0)
            lig_adi = mac.get("league", {}).get("name", "Dünya Ligi")
            dakika = mac.get("minute", "Canlı")

            # Hafıza Anahtarı: Maç ID + Ev Skor + Deplasman Skor
            # Skor 0-0 iken 1-0 olursa veya maç yeni başlarsa ANINDA BİLDİRİR
            mac_key = f"{mac_id}_{skor_ev}-{skor_dep}"

            if mac_key in bildirilen_maclar:
                continue # Bu skor zaten bildirildiyse es geç

            mesaj = (
                f"🚨 **GOL / CANLI MAÇ BİLDİRİMİ!**\n\n"
                f"🏆 **Lig:** {lig_adi}\n"
                f"⚽ **Maç:** {ev} {skor_ev} - {skor_dep} {dep}\n"
                f"⏱️ **Dakika:** {dakika}'\n\n"
                f"🔥 *Maçkolik Anlık Canlı Akış*"
            )

            telegram_bildir(mesaj)
            bildirilen_maclar.add(mac_key)
            time.sleep(1) # Telegram engelini önlemek için kısa bekleme

    except Exception as e:
        print("Sistem Tarama Hatası:", e)

# Web sunucusunu arka planda çalıştır
threading.Thread(target=run_dummy_server, daemon=True).start()

print("🚀 Filtresiz Garanti Gol Radarı Başlatıldı!")
telegram_bildir("⚡ **Filtresiz Canlı Radar Aktif!**\nHizmetsiz/Filtresiz tüm canlı maçlar ve goller anında cebinizde.")

while True:
    mackolik_garanti_tara()
    time.sleep(45) # Her 45 saniyede bir canlının kalbini kontrol eder
