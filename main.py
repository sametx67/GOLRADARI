import os
import requests
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

BOT_TOKEN = "8656415127:AAHkqmZdW0b2NGzqRb-iRqhCkUNG4SwAN1w"
CHAT_ID = "8210045794"

# Bildirilen sinyalleri tekrar atmamak için hafıza
bildirilen_analizler = set()

class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Dakikasiz Gol Radari Aktif!")

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

def sofascore_analiz_tara():
    global bildirilen_analizler
    url = "https://api.sofascore.com/api/v1/sport/football/events/live"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
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

            # Detaylı İstatistik İsteği (Şut, İsabetli Şut, Korner)
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

            # DAKİKASIZ BASKI ALGORİTMASI:
            # Hangi dakikada olursa olsun (Top. Şut >= 6 veya İsabetli >= 3 veya Korner >= 4)
            baski_var_mi = (toplam_sut >= 6) or (isabetli_sut >= 3) or (korner >= 4)

            analiz_key = f"{event_id}_{skor_ev}_{skor_dep}"

            if baski_var_mi and (analiz_key not in bildirilen_analizler):
                mesaj = (
                    f"🔥 **YÜKSEK GOL İHTİMALİ SİNYALİ!**\n\n"
                    f"🏆 **Lig:** {lig_adi}\n"
                    f"⚽ **Maç:** {ev} {skor_ev} - {skor_dep} {dep}\n"
                    f"⏱️ **Dakika:** {dakika}'\n\n"
                    f"📊 **CANLI BASKI İSTATİSTİKLERİ:**\n"
                    f"🎯 **Toplam Şut:** {toplam_sut}\n"
                    f"🎯 **İsabetli Şut:** {isabetli_sut}\n"
                    f"⛳ **Korner:** {korner}\n\n"
                    f"⚠️ *Dakika fark etmeksizin yoğun baskı var, gol gelebilir!*"
                )
                telegram_bildir(mesaj)
                bildirilen_analizler.add(analiz_key)
                time.sleep(2)

    except Exception as e:
        print("Analiz Hatası:", e)

# Web sunucusunu başlat
threading.Thread(target=run_dummy_server, daemon=True).start()

print("🚀 Dakikasız Gol İhtimali Radarı Başlatıldı!")
telegram_bildir("⚡ **Tüm Dakikalar Kapsama Alanında!**\nMaçın her anındaki baskılar radara takılacak.")

while True:
    sofascore_analiz_tara()
    time.sleep(120)  # Her 2 dakikada bir tüm canlı maçları tarar
