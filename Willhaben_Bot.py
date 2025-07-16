import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import time

# === Lade Umgebungsvariablen ===
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SEARCH_URLS = [
    "https://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz/kameras-camcorder/digitalkameras-6900?keyword=sony&sfId=1de90525-ce04-4ed0-998a-0dc28e16bb28&rows=30&isNavigation=true",
    "https://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz/kameras-camcorder/digitalkameras-6900?keyword=nikon&sfId=86a4c4a1-d4d7-4a83-b8e0-35a60c952684&rows=30&isNavigation=true&PRICE_TO=40",
    "https://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz/kameras-camcorder/digitalkameras-6900?sfId=86a4c4a1-d4d7-4a83-b8e0-35a60c952684&rows=30&isNavigation=true&keyword=canon&PRICE_FROM=0&PRICE_TO=40",
    "https://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz/kameras-camcorder/digitalkameras-6900?sfId=86a4c4a1-d4d7-4a83-b8e0-35a60c952684&rows=30&isNavigation=true&keyword=kamera&PRICE_FROM=0&PRICE_TO=40",
    "https://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz?isNavigation=true&srcType=vertical-search-box&keyword=Nintendo",
    "https://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz?isNavigation=true&srcType=vertical-search-box&keyword=Gameboy",
    "https://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz?isNavigation=true&srcType=vertical-search-box&keyword=gamecube",
    "https://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz?isNavigation=true&srcType=vertical-search-box&keyword=pokemon"
]

BLACKLIST = [
    "rollei", "agfa", "pixica", "polaroid", "analog", "minolta",
    "zwischenring", "blende", "lens", "ips", "sammlung", "fernauslöser",
    "pentax", "kodak", "funko", "objektiv", "filter", "fernseher", "karten"
]

SEEN_ADS_FILE = "seen_ads.txt"
INTERVAL_SECONDS = 60

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        print(f"❌ Telegram-Fehler: {response.text}")

def load_seen_ads():
    try:
        with open(SEEN_ADS_FILE, "r") as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def save_seen_ads(seen_ads):
    with open(SEEN_ADS_FILE, "w") as f:
        f.write("\n".join(seen_ads))

def is_blacklisted(text):
    text_lower = text.lower()
    return any(bad_word in text_lower for bad_word in BLACKLIST)

seen_ads = load_seen_ads()

while True:
    for url in SEARCH_URLS:
        print(f"🔍 Suche: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
        except Exception as e:
            print(f"❌ Fehler: {e}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        ads = soup.find_all("div", {"class": "Box-sc-wfmb7k-0 sc-85abcb49-0 cYZWGI kiHUOb"})

        for ad in ads:
            link_tag = ad.find("a", href=True)
            if not link_tag:
                continue
            link = "https://www.willhaben.at" + link_tag["href"]
            if link in seen_ads:
                continue

            title_tag = ad.find("h3")
            title = title_tag.get_text(strip=True) if title_tag else "Kein Titel"
            price_tag = ad.find("div", {"class": "Box-sc-wfmb7k-0 sc-6ef645b-0 dTgjTZ"})
            price = price_tag.get_text(strip=True) if price_tag else "Preis unbekannt"

            if is_blacklisted(title):
                print(f"🚫 Blacklist: {title}")
                seen_ads.add(link)
                continue

            message = f"{title}\n{price}\n{link}"
            print(f"🆕 Neuer Treffer:\n{message}")
            send_telegram(message)
            seen_ads.add(link)

    save_seen_ads(seen_ads)
    print(f"⏳ Warte {INTERVAL_SECONDS} Sekunden…\n")
    time.sleep(INTERVAL_SECONDS)
