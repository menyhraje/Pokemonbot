import requests
from bs4 import BeautifulSoup
import time
import os
import re

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

SEARCH_TERM = ""
SEARCH_URLS = []
sent_links = set()
last_update_id = None
RUNNING = False


# 📩 posílání zpráv
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=data)


# 📥 čtení zpráv
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


# 💸 najde cenu
def get_price(text):
    matches = re.findall(r'(\d{3,5})\s?kč', text)

    if matches:
        prices = [int(p) for p in matches if int(p) > 50]
        if prices:
            return min(prices)

    return "neznámá"


# 🔍 kontrola webů
def check_sites():
    global sent_links

    for url in SEARCH_URLS:
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(r.text, "html.parser")
            text = soup.get_text().lower()

            links = soup.find_all("a", href=True)

            for link in links:
                href = link["href"]

                if any(x in href.lower() for x in ["pokemon", "trainer", "box"]):

                    full_link = href if href.startswith("http") else url + href

                    if full_link not in sent_links:

                        if any(word in text for word in ["skladem", "in stock", "dostupné"]):
                            price = get_price(text)

                            send_telegram(f"🔥 RESTOCK!\n{full_link}\n💸 Cena: {price} Kč")

                            sent_links.add(full_link)

        except Exception as e:
            print("chyba:", e)


# 🤖 START MESSAGE
send_telegram("🤖 Bot spuštěn! Napiš co chceš hledat (nebo 'stop').")


# 🔁 MAIN LOOP
while True:
    try:
        global RUNNING
        
        msg = get_updates()

        if msg:
            if msg == "stop":
                RUNNING = False
                send_telegram("🛑 Hledání zastaveno")

            elif msg == "status":
                send_telegram(f"📊 Stav: {'běží' if RUNNING else 'zastaveno'}")

            else:
                RUNNING = True
                SEARCH_TERM = msg
                SEARCH_URLS = build_search_urls(msg)
                sent_links.clear()

                send_telegram(f"🔍 Sleduju: {SEARCH_TERM}")

        if RUNNING and SEARCH_URLS:
            check_sites()
        else:
            print("⏸️ Pauza...")

        time.sleep(60)

    except Exception as e:
        print("error:", e)
        time.sleep(60)
