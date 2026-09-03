import os
import sys
import subprocess

# Kütüphaneler eksikse otomatik kuran sistem
try:
    from flask import Flask
    import requests
except ModuleNotFoundError:
    print("Kütüphaneler eksik, otomatik kuruluyor...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "requests"])
    from flask import Flask
    import requests

import time
import threading

# Render Port Zorunluluğu İçin Flask Sunucusu
app = Flask(__name__)

@app.route('/')
def home():
    return "Gol Radari Aktif!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Web sunucusunu arka planda başlat
threading.Thread(target=run_flask, daemon=True).start()

# Telegram Ayarları
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8656415127:AAHkqmZdW0b2NGzqRb-iRqhCkUNG4SwAN1w")
CHAT_ID = "8210045794"

bildirilen_baskilar = set()

def telegram_bildir(mesaj):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("Telegram hatasi:", e)

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
            return

        data = response.json()
        matches = data.get("data", [])
        
        canli_maclar = [m for m in matches if m.get("status", {}).get("isLive", False)]

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
        print("Tarama Hatasi:", e)

# Onay Bildirimi
telegram_bildir("🚀 **Dakikasız Gol Radarı Tam Performans Devrede!**\nKütüphane ve port sorunları aşıldı, canlı maçlar taranıyor.")

# Ana Tarama Döngüsü
while True:
    try:
        gol_radari_tara()
    except Exception as e:
        print("Döngü Hatasi:", e)
    time.sleep(60)
