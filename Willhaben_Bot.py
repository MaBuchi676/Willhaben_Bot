import requests
from bs4 import BeautifulSoup
import time
import sys

# === Einstellungen ===

SEARCH_URLS = [
    "https://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz/kameras-camcorder/digitalkameras-6900?keyword=sony&sfId=1de90525-ce04-4ed0-998a-0dc28e16bb28&rows=30&isNavigation=true",
    "https://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz/kameras-camcorder/digitalkameras-6900?keyword=nikon&sfId=86a4c4a1-d4d7-4a83-b8e0-35a60c952684&rows=30&isNavigation=true&PRICE_TO=40",
    "https://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz/kameras-camcorder/digitalkameras-6900?sfId=86a4c4a1-d4d7-4a83-b8e0-35a60c952684&rows=30&isNavigation=true&keyword=canon&PRICE_FROM=0&PRICE_TO=40",
    "https://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz/kameras-camcorder/digitalkameras-6900?sfId=86a4c4a1-d4d7-4a83-b8e0-35a60c952684&rows=30&isNavigation=true&keyword=kamera&PRICE_FROM=0&PRICE_TO=40",
    "https://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz?isNavigation=true&srcType=vertical-search-box&keyword=Nintendo",
    "https://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz?isNavigation=true&srcType=vertical-search-box&keyword=Gameboy",
    "https://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz?isNavigation=true&srcType=vertical-search-box&keyword=gamecube",
    "https://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz/games-konsolen-2785?keyword=pokemon&sfId=7e6c5bc6-2f89-4e03-9fab-e80438b6f2d7&rows=30&isNavigation=true"
]

INTERVAL_SECONDS = 60
SEEN_ADS_FILE = "seen_ads.txt"

TELEGRAM_BOT_TOKEN = "7704934659:AAHbcd48ahTMuMQfkEuOqzBqUcyL0_fz4Ac"
TELEGRAM_CHAT_ID = "8135817857"

BLACKLIST = [
    "rollei", "agfa", "pixica", "polaroid", "analog",
    "minolta", "zwischenring", "blende", "lens", "ips",
    "sammlung", "fernauslöser", "pentax", "kodak",
    "funko", "objektiv", "filter", "fernseher", "karten"
]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print(f"❌ Telegram-Fehler: {response.text}")
    except Exception as e:
        print(f"❌ Telegram-Exception: {e}")

def load_seen_ads():
    try:
        with open(SEEN_ADS_FILE, "r") as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def save_seen_ads(seen_ads):
    with open(SEEN_ADS_FILE, "w") as f:
        f.write("\n".join(seen_ads))

def clear_seen_ads():
    open(SEEN_ADS_FILE, "w").close()
    print("🗑️ Gesehene Anzeigen zurückgesetzt.")

def run_bot():
    seen_ads = load_seen_ads()
    print("🚀 Bot gestartet …")
    while True:
        for url in SEARCH_URLS:
            print(f"🔍 {url}")
            try:
                r = requests.get(url)
                r.raise_for_status()
            except Exception as e:
                print(f"❌ Fehler beim Abruf: {e}")
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            ads = soup.find_all("div", class_="Box-sc-wfmb7k-0 sc-85abcb49-0 cYZWGI kiHUOb")

            new_count = 0
            for ad in ads:
                link_tag = ad.find("a", href=True)
                if not link_tag:
                    continue
                link = "https://www.willhaben.at" + link_tag["href"]
                if link in seen_ads:
                    continue

                title_tag = ad.find("h3")
                title = title_tag.get_text(strip=True) if title_tag else "Kein Titel"
                price_tag = ad.find("div", class_="search-result-price")
                price = price_tag.get_text(strip=True) if price_tag else "Preis unbekannt"

                if any(word in title.lower() for word in BLACKLIST):
                    print(f"🚫 Ignoriert (Blacklist): {title}")
                    continue

                message = f"{title}\n{price}\n{link}"
                print(f"🆕 {message}")
                send_telegram(message)
                seen_ads.add(link)
                new_count += 1

            if new_count == 0:
                print("ℹ️ Keine neuen Anzeigen.")
        save_seen_ads(seen_ads)
        print(f"⏳ Warte {INTERVAL_SECONDS} Sek …")
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        clear_seen_ads()
    run_bot()
