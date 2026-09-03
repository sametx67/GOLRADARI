import os
import requests
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

# 1. RENDER PORT BINDING (Erken kapanmayı önleyen sunucu)
def start_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"Port {port} dinleniyor...")
    server.serve_forever()

# Port dinleyicisini Python başlar başlamaz ilk satırda çalıştır
t = threading.Thread(target=start_server, daemon=True)
t.start()

# Environment variable'dan Token çek, yoksa varsayılanı kullan
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8656415127:AAHkqmZdW0b2NGzqRb-iRqhCkUNG4SwAN1w")
CHAT_ID = "8210045794"

bildirilen_baskilar = set()

def telegram_bildir(mesaj):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, data=payload, timeout=10)
        print(f"Telegram Gönderim Yanıtı: {res.status_code}")
    except Exception as e:
        print("Telegram hatası:", e)

def gol_radari_tara():
    global bildirilen_baskilar
    url = "https://m.mackolik.com/api/livematches"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
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
        print(f"🟢 Taranan Canlı Maç Sayısı: {len(canli_maclar)}")

        for mac in canli_maclar:
            mac_id = mac.get("id")
            ev = mac.get("homeTeam", {}).get("name", "Ev")
            dep = mac.get("awayTeam", {}).get("name", "Dep")
            skor_ev = mac.get("score", {}).get("home", 0) or 0
            skor_dep = mac.get("score", {}).get("away", 0) or 0
            lig_adi = mac.get("league", {}).get("name", "Dünya Ligi")
            dakika = mac.get("minute", "Canlı")

            stats = mac.get("stats", {}) or {}
            
            try:
                top_sut_ev = int(stats.get("totalShotsHome", 0) or 0)
                top_sut_dep = int(stats.get("totalShotsAway", 0) or 0)
                is_sut_ev = int(stats.get("shotsOnTargetHome", 0) or 0)
                is_sut_dep = int(stats.get("shotsOnTargetAway", 0) or 0)
                korner_ev = int(stats.get("cornerKicksHome", 0) or 0)
                korner_dep = int(stats.get("cornerKicksAway", 0) or 0)
            except Exception:
                continue

            toplam_sut = top_sut_ev + top_sut_dep
            isabetli_sut = is_sut_ev + is_sut_dep
            toplam_korner = korner_ev + korner_dep

            # DAKİKASIZ BASKI FİLTRESİ
            baski_var = (isabetli_sut >= 2) or (toplam_sut >= 6) or (toplam_korner >= 4)

            if not baski_var:
                continue

            baski_key = f"{mac_id}_{skor_ev}-{skor_dep}_IS:{isabetli_sut}_TS:{toplam_sut}_K:{toplam_korner}"

            if baski_key in bildirilen_baskilar:
                continue

            mesaj = (
                f"🔥 **GOL OLMA İHTİMALİ ÇOK YÜKSEK!**\n\n"
                f"🏆 **Lig:** {lig_adi}\n"
                f"⚽ **Maç:** {ev} {skor_ev} - {skor_dep} {dep}\n"
                f"⏱️ **Dakika:** {dakika}'\n\n"
                f"📊 **CANLI BASKI VERİLERİ:**\n"
                f"🎯 **İsabetli Şut:** {isabetli_sut}\n"
                f"🎯 **Toplam Şut:** {toplam_sut}\n"
                f"⛳ **Korner:** {toplam_korner}\n\n"
                f"⚠️ *Dakika fark etmeksizin yoğun baskı var! Gol gelebilir!*"
            )

            telegram_bildir(mesaj)
            bildirilen_baskilar.add(baski_key)
            time.sleep(2)

    except Exception as e:
        print("Tarama Hatası:", e)

# Uygulama başladığında Telegram bildirimini at
print("🚀 Gol Radarı Başlatıldı!")
telegram_bildir("🚀 **Dakikasız Gol Baskı Radarı Yayında!**\nSistem başarıyla kuruldu, 7/24 canlı maçlar taranıyor.")

# Ana döngü
while True:
    try:
        gol_radari_tara()
    except Exception as e:
        print("Döngü Hatası:", e)
    time.sleep(60)
