import requests
from bs4 import BeautifulSoup
import time
import os

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

SEARCH_TERM = ""
SEARCH_URLS = []
sent_links = set()
last_update_id = None


# 📩 posílání zpráv
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=data)


# 📥 čtení zpráv z Telegramu
def get_updates():
    global last_update_id
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

    if last_update_id:
        url += f"?offset={last_update_id + 1}"

    response = requests.get(url).json()

    if "result" in response:
        for update in response["result"]:
            last_update_id = update["update_id"]

            if "message" in update and "text" in update["message"]:
                return update["message"]["text"].lower()

    return None


# 🔍 vytvoření search URL
def build_search_urls(term):
    term = term.replace(" ", "+")
    return [
        f"https://www.dracik.cz/hledej?q={term}",
        f"https://www.shadowball.cz/search?q={term}",
        f"https://www.vesely-drak.cz/hledat?search={term}",
        f"https://www.tlamagames.com/cz/hledani?phrase={term}",
        f"https://www.originalky.cz/vyhledavani/?q={term}"
    ]


# 💸 najde cenu (pokud je na stránce)
def get_price(text):
    import re
    match = re.search(r'(\d{2,5})\s?kč', text)
    if match:
        return match.group(1)
    return "neznámá"


# 🔍 kontrola stránky
def check_sites():
    global sent_links

    for url in SEARCH_URLS:
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            text = r.text.lower()

            if any(word in text for word in ["skladem", "in stock", "dostupné", "available"]):
                
                if url not in sent_links:
                    price = get_price(text)

                    send_telegram(f"🔥 RESTOCK!\n{url}\n💸 Cena: {price} Kč")
                    sent_links.add(url)

            else:
                print("není skladem:", url)

        except Exception as e:
            print("chyba:", e)


# 🔁 MAIN LOOP
send_telegram("🤖 Bot spuštěn! Napiš co chceš hledat.")

while True:
    try:
        msg = get_updates()

        if msg:
            SEARCH_TERM = msg
            SEARCH_URLS = build_search_urls(msg)
            sent_links.clear()

            send_telegram(f"🔍 Sleduju: {SEARCH_TERM}")

        if SEARCH_URLS:
            check_sites()

        print("čekám 60s...")
        time.sleep(60)

    except Exception as e:
        print("error:", e)
        time.sleep(60)
