import requests
import time

BOT_TOKEN = "8656415127:AAHkqmZdW0b2NGzqRb-iRqhCkUNG4SwAN1w"
CHAT_ID = "8210045794"

def telegram_bildir(mesaj):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print("Telegram hatası:", e)

def mackolik_canli_tara():
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
        
        for mac in matches:
            durum = mac.get("status", {})
            if not durum.get("isLive", False):
                continue

            ev = mac.get("homeTeam", {}).get("name", "Ev")
            dep = mac.get("awayTeam", {}).get("name", "Dep")
            skor_ev = mac.get("score", {}).get("home", 0)
            skor_dep = mac.get("score", {}).get("away", 0)
            lig_adi = mac.get("league", {}).get("name", "Dünya Ligi")
            dakika = mac.get("minute", "Canlı")

            mesaj = (
                f"🚨 **MAÇKOLİK CANLI GOL RADARI**\n\n"
                f"🏆 **Lig:** {lig_adi}\n"
                f"⚽ **Maç:** {ev} {skor_ev} - {skor_dep} {dep}\n"
                f"⏱️ **Dakika:** {dakika}'\n\n"
                f"🔥 *Sınırsız Canlı Takip: Brezilya, Arjantin ve Tüm Dünya!*"
            )
            telegram_bildir(mesaj)
            time.sleep(1)
    except Exception as e:
        print("Hata:", e)

print("🚀 Sınırsız Radar Başlatıldı!")
while True:
    mackolik_canli_tara()
    time.sleep(180)