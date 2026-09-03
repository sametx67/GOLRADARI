import os
import requests
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

BOT_TOKEN = "8656415127:AAHkqmZdW0b2NGzqRb-iRqhCkUNG4SwAN1w"
CHAT_ID = "8210045794"

# Sinyal verilen maçları tekrar tekrar atmamak için hafıza
bildirilen_sinyaller = set()

class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Gol Sinyali Radari Aktif!")

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
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("Telegram hatası:", e)

def gol_sinyali_tara():
    global bildirilen_sinyaller
    url = "https://api.sofascore.com/api/v1/sport/football/events/live"
    
    # Sofascore engelini aşmak için gelişmiş tarayıcı kimliği
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.sofascore.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"API Bağlantı Durumu: {response.status_code}")
            return

        events = response.json().get("events", [])
        
        for event in events:
            event_id = event.get("id")
            ev = event.get("homeTeam", {}).get("name", "Ev")
            dep = event.get("awayTeam", {}).get("name", "Dep")
            skor_ev = event.get("homeScore", {}).get("current", 0)
            skor_dep = event.get("awayScore", {}).get("current", 0)
            lig_adi = event.get("tournament", {}).get("name", "Canlı Lig")
            dakika = event.get("time", {}).get("played", "Canlı")

            # Maçın Detaylı Şut/Korner İstatistiğini Çek
            stats_url = f"https://api.sofascore.com/api/v1/event/{event_id}/statistics"
            stats_res = requests.get(stats_url, headers=headers, timeout=5)
            
            toplam_sut = 0
            isabetli_sut = 0
            korner = 0

            if stats_res.status_code == 200:
                stats_data = stats_res.json().get("statistics", [])
                if stats_data:
                    groups = stats_data[0].get("groups", [])
                    for group in groups:
                        for item in group.get("statisticsItems", []):
                            name = item.get("name")
                            h_val = int(item.get("home", 0))
                            a_val = int(item.get("away", 0))
                            
                            if name == "Total shots":
                                toplam_sut = h_val + a_val
                            elif name == "Shots on target":
                                isabetli_sut = h_val + a_val
                            elif name == "Corner kicks":
                                korner = h_val + a_val

            # GOL ÖNCESİ SİNYAL ALGORİTMASI
            sinyal_seviyesi = None
            
            # Çok Yüksek İhtimal
            if isabetli_sut >= 4 or toplam_sut >= 9 or korner >= 6:
                sinyal_seviyesi = "🔴 **ÇOK YÜKSEK GOL İHTİMALİ! (KALE ABLUKADA)**"
            # Yüksek İhtimal
            elif isabetli_sut >= 2 or toplam_sut >= 6 or korner >= 4:
                sinyal_seviyesi = "🟡 **YÜKSEK GOL İHTİMALİ (BASKI ARTIYOR)**"

            # Şartlar sağlanmıyorsa MAÇI ATLA, Telegram'a hiçbir şey atma
            if not sinyal_seviyesi:
                continue

            # Sinyal Anahtarı (Aynı maçın aynı skorundaki baskıyı 1 kere bildirir)
            sinyal_key = f"{event_id}_{skor_ev}-{skor_dep}_{sinyal_seviyesi}"

            if sinyal_key in bildirilen_sinyaller:
                continue

            mesaj = (
                f"{sinyal_seviyesi}\n\n"
                f"🏆 **Lig:** {lig_adi}\n"
                f"⚽ **Maç:** {ev} {skor_ev} - {skor_dep} {dep}\n"
                f"⏱️ **Dakika:** {dakika}'\n\n"
                f"📊 **CANLI BASKI VERİLERİ:**\n"
                f"🎯 **Isabetli Şut:** {isabetli_sut}\n"
                f"🎯 **Toplam Şut:** {toplam_sut}\n"
                f"⛳ **Korner:** {korner}\n\n"
                f"💡 *Gol Olmadan Önce Canlı Bahis Sinyali!*"
            )

            telegram_bildir(mesaj)
            bildirilen_sinyaller.add(sinyal_key)
            time.sleep(2)

    except Exception as e:
        print("Sinyal Tarama Hatası:", e)

# Web sunucusunu çalıştır
threading.Thread(target=run_dummy_server, daemon=True).start()

print("🚀 Gol Sinyali Radarı Başlatıldı!")
telegram_bildir("🚨 **Gol Öncesi Canlı Bahis Sinyal Radarı Devrede!**\nSadece şut ve korner baskısı tavan yapan maçlar bildirilecek.")

while True:
    gol_sinyali_tara()
    time.sleep(60) # Her 60 saniyede bir tüm canlı maçların istatistiklerini süzgeçten geçirir
