import os
import requests
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

BOT_TOKEN = "8656415127:AAHkqmZdW0b2NGzqRb-iRqhCkUNG4SwAN1w"
CHAT_ID = "8210045794"

# Bildirilen maçları hafızada tutmak için küme
bildirilen_maclar = set()

class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Gol Radari Aktif!")

    def log_message(self, format, *args):
        return

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyServer)
    print(f"🌐 Web sunucusu {port} portunda başlatıldı.")
    server.serve_forever()

def telegram_bildir(mesaj):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, data=payload, timeout=10)
        print(f"Telegram Gönderim Yanıtı: {res.status_code}")
        if res.status_code != 200:
            print("Telegram Detay:", res.text)
    except Exception as e:
        print("Telegram bağlantı hatası:", e)

def mackolik_canli_tara():
    global bildirilen_maclar
    url = "https://m.mackolik.com/api/livematches"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://m.mackolik.com/"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Maçkolik Yanıt Verme Hatası: {response.status_code}")
            return

        data = response.json()
        matches = data.get("data", [])
        
        canli_maclar = [m for m in matches if m.get("status", {}).get("isLive", False)]
        print(f"📊 Taranan Canlı Maç Sayısı: {len(canli_maclar)}")

        for mac in canli_maclar:
            mac_id = mac.get("id")
            
            # Sadece yeni/farklı canlı maçları veya skor değişimlerini yakalar
            ev = mac.get("homeTeam", {}).get("name", "Ev")
            dep = mac.get("awayTeam", {}).get("name", "Dep")
            skor_ev = mac.get("score", {}).get("home", 0)
            skor_dep = mac.get("score", {}).get("away", 0)
            
            mac_anahtar = f"{mac_id}_{skor_ev}_{skor_dep}"
            
            if mac_anahtar in bildirilen_maclar:
                continue # Zaten bildirildiyse tekrar atıp spama düşme
                
            lig_adi = mac.get("league", {}).get("name", "Dünya Ligi")
            dakika = mac.get("minute", "Canlı")

            mesaj = (
                f"🚨 **CANLI MAÇ RADARI**\n\n"
                f"🏆 **Lig:** {lig_adi}\n"
                f"⚽ **Maç:** {ev} {skor_ev} - {skor_dep} {dep}\n"
                f"⏱️ **Dakika:** {dakika}'\n\n"
                f"🔥 *Maçkolik Canlı Akış*"
            )
            telegram_bildir(mesaj)
            bildirilen_maclar.add(mac_anahtar)
            time.sleep(2) # Spama düşmemek için 2 saniye bekleme

    except Exception as e:
        print("Maçkolik Çekim Hatası:", e)

# Web sunucusunu başlat
threading.Thread(target=run_dummy_server, daemon=True).start()

print("🚀 Sınırsız Radar Başlatıldı! İlk test bildirimi gönderiliyor...")
telegram_bildir("🤖 **Gol Radarı Render Üzerinde Başarıyla Çalıştı!**\nCanlı maçlar taranıyor...")

while True:
    mackolik_canli_tara()
    time.sleep(180)
