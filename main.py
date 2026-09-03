import os
import requests
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

BOT_TOKEN = "8656415127:AAHkqmZdW0b2NGzqRb-iRqhCkUNG4SwAN1w"
CHAT_ID = "8210045794"

# Bildirilen maç ve istatistik durumlarını hafızada tutan küme
bildirilen_durumlar = set()

class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Anlik Sut/Korner Radari Aktif!")

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
        print(f"Telegram Gönderim Yanıtı: {res.status_code}")
    except Exception as e:
        print("Telegram hatası:", e)

def mackolik_canli_tara():
    global bildirilen_durumlar
    url = "https://m.mackolik.com/api/livematches"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://m.mackolik.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Maçkolik Bağlantı Hatası: {response.status_code}")
            return

        data = response.json()
        matches = data.get("data", [])
        
        canli_maclar = [m for m in matches if m.get("status", {}).get("isLive", False)]
        print(f"📊 Maçkolik Canlı Maç Sayısı: {len(canli_maclar)}")

        for mac in canli_maclar:
            mac_id = mac.get("id")
            ev = mac.get("homeTeam", {}).get("name", "Ev")
            dep = mac.get("awayTeam", {}).get("name", "Dep")
            skor_ev = mac.get("score", {}).get("home", 0)
            skor_dep = mac.get("score", {}).get("away", 0)
            lig_adi = mac.get("league", {}).get("name", "Dünya Ligi")
            dakika = mac.get("minute", "Canlı")

            # İstatistik verilerini al
            stats = mac.get("stats", {})
            toplam_sut_ev = stats.get("totalShotsHome", "-")
            toplam_sut_dep = stats.get("totalShotsAway", "-")
            isabetli_sut_ev = stats.get("shotsOnTargetHome", "-")
            isabetli_sut_dep = stats.get("shotsOnTargetAway", "-")
            korner_ev = stats.get("cornerKicksHome", "-")
            korner_dep = stats.get("cornerKicksAway", "-")

            # Hafıza Anahtarı: Skor + Şut + Korner değişirse YENİ BİLDİRİM AT
            durum_anahtari = f"{mac_id}_S:{skor_ev}-{skor_dep}_TS:{toplam_sut_ev}-{toplam_sut_dep}_IS:{isabetli_sut_ev}-{isabetli_sut_dep}_K:{korner_ev}-{korner_dep}"

            if durum_anahtari in bildirilen_durumlar:
                continue

            # İstatistik Metni
            istatistik_text = ""
            if toplam_sut_ev != "-" and toplam_sut_dep != "-":
                istatistik_text += f"🎯 **Toplam Şut:** {toplam_sut_ev} - {toplam_sut_dep}\n"
            if isabetli_sut_ev != "-" and isabetli_sut_dep != "-":
                istatistik_text += f"🔥 **İsabetli Şut:** {isabetli_sut_ev} - {isabetli_sut_dep}\n"
            if korner_ev != "-" and korner_dep != "-":
                istatistik_text += f"⛳ **Korner:** {korner_ev} - {korner_dep}\n"

            mesaj = (
                f"🚨 **CANLI MAÇ & İSTATİSTİK GÜNCELLEMESİ**\n\n"
                f"🏆 **Lig:** {lig_adi}\n"
                f"⚽ **Maç:** {ev} {skor_ev} - {skor_dep} {dep}\n"
                f"⏱️ **Dakika:** {dakika}'\n"
            )

            if istatistik_text:
                mesaj += f"\n📊 **ANLIK İSTATİSTİK:**\n{istatistik_text}"

            mesaj += f"\n⚡ *Maçkolik Anlık Şut/Korner Radarı*"

            telegram_bildir(mesaj)
            bildirilen_durumlar.add(durum_anahtari)
            time.sleep(2)

    except Exception as e:
        print("Maçkolik Çekim Hatası:", e)

# Web sunucusunu başlat
threading.Thread(target=run_dummy_server, daemon=True).start()

print("🚀 Anlık Şut ve Korner Takipli Radar Başlatıldı!")
telegram_bildir("🎯 **Anlık Şut & Korner Takibi Aktif!**\nŞut veya korner sayıları arttıkça canlı bildirim düşecek.")

while True:
    mackolik_canli_tara()
