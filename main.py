import os
import requests
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

BOT_TOKEN = "8656415127:AAHkqmZdW0b2NGzqRb-iRqhCkUNG4SwAN1w"
CHAT_ID = "8210045794"

# Bildirilen baskı durumlarını tekrar atmamak için hafıza
bildirilen_baskilar = set()

class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Gol Öncesi Baski Radari Aktif!")

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

def mackolik_baski_tara():
    global bildirilen_baskilar
    url = "https://m.mackolik.com/api/livematches"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://m.mackolik.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return

        data = response.json()
        matches = data.get("data", [])
        
        canli_maclar = [m for m in matches if m.get("status", {}).get("isLive", False)]

        for mac in canli_maclar:
            mac_id = mac.get("id")
            ev = mac.get("homeTeam", {}).get("name", "Ev")
            dep = mac.get("awayTeam", {}).get("name", "Dep")
            skor_ev = mac.get("score", {}).get("home", 0)
            skor_dep = mac.get("score", {}).get("away", 0)
            lig_adi = mac.get("league", {}).get("name", "Dünya Ligi")
            dakika = mac.get("minute", "Canlı")

            # İstatistik verilerini sayıya çevir
            stats = mac.get("stats", {})
            try:
                top_sut_ev = int(stats.get("totalShotsHome", 0) or 0)
                top_sut_dep = int(stats.get("totalShotsAway", 0) or 0)
                is_sut_ev = int(stats.get("shotsOnTargetHome", 0) or 0)
                is_sut_dep = int(stats.get("shotsOnTargetAway", 0) or 0)
                korner_ev = int(stats.get("cornerKicksHome", 0) or 0)
                korner_dep = int(stats.get("cornerKicksAway", 0) or 0)
            except ValueError:
                continue

            toplam_sut = top_sut_ev + top_sut_dep
            toplam_isabetli = is_sut_ev + is_sut_dep
            toplam_korner = korner_ev + korner_dep

            # GOL OLMA İHTİMALİ & BASKI FİLTRESİ
            # Maçta baskı var mı? (Toplam Şut >= 5 VEYA İsabetli Şut >= 2 VEYA Korner >= 3)
            baski_var = (toplam_sut >= 5) or (toplam_isabetli >= 2) or (toplam_korner >= 3)

            if not baski_var:
                continue # Baskı yoksa uyarım atma, pas geç

            # Baskı Seviyesi Belirleme
            seviye = "🔥 ORTA BASKI"
            if toplam_isabetli >= 4 or toplam_sut >= 10 or toplam_korner >= 6:
                seviye = "🚨 YÜKSEK GOL İHTİMALİ / ŞİDDETLİ BASKI"

            # Hafıza anahtarı (Aynı baskı durumunu tekrar tekrar atmamak için)
            baski_key = f"{mac_id}_{skor_ev}-{skor_dep}_TS:{toplam_sut}_IS:{toplam_isabetli}_K:{toplam_korner}"

            if baski_key in bildirilen_baskilar:
                continue

            mesaj = (
                f"{seviye}\n\n"
                f"🏆 **Lig:** {lig_adi}\n"
                f"⚽ **Maç:** {ev} {skor_ev} - {skor_dep} {dep}\n"
                f"⏱️ **Dakika:** {dakika}'\n\n"
                f"📊 **CANLI BASKI VERİLERİ:**\n"
                f"🎯 **Toplam Şut:** {toplam_sut} ({top_sut_ev} - {top_sut_dep})\n"
                f"🔥 **İsabetli Şut:** {toplam_isabetli} ({is_sut_ev} - {is_sut_dep})\n"
                f"⛳ **Korner:** {toplam_korner} ({korner_ev} - {korner_dep})\n\n"
                f"⚡ *Gol Gelmeden Önceki Baskı Sinyali!*"
            )

            telegram_bildir(mesaj)
            bildirilen_baskilar.add(baski_key)
            time.sleep(2)

    except Exception as e:
        print("Baskı Tarama Hatası:", e)

# Web sunucusunu başlat
threading.Thread(target=run_dummy_server, daemon=True).start()

print("🚀 Gol Öncesi Baskı Radarı Başlatıldı!")
telegram_bildir("🎯 **Gol Öncesi Baskı Radarı Devrede!**\nSadece şut ve korner baskısı tavan yapan, gol ihtimali yüksek maçlar bildirilecek.")

while True:
    mackolik_baski_tara()
    time.sleep(60) # Her 1 dakikada bir baskılı maçları tarar
