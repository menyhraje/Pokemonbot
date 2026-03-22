import requests
from bs4 import BeautifulSoup
import time
import os
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

search_tasks = {}  # {"term": {"urls": [], "min": 0, "max": 999999}}
sent_links = set()
last_update_id = None


# 📩 Telegram
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)


# 📥 zprávy
def get_updates():
    global last_update_id
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

    if last_update_id:
        url += f"?offset={last_update_id + 1}"

    response = requests.get(url).json()
    messages = []

    if "result" in response:
        for update in response["result"]:
            last_update_id = update["update_id"]

            if "message" in update and "text" in update["message"]:
                text = update["message"]["text"].lower()
                print("📩 ZPRÁVA:", text)
                messages.append(text)

    return messages


# 🔍 relevance (LEVEL 1)
def is_relevant(text, term):
    keywords = term.lower().split()
    match_count = sum(1 for word in keywords if word in text)
    return match_count >= max(2, len(keywords) // 2)


# 🎯 typ produktu (LEVEL 2)
PRODUCT_TYPES = ["etb", "elite trainer box", "booster", "bundle"]

def has_product_type(text):
    return any(p in text for p in PRODUCT_TYPES)


# 💸 cena parser
def get_price(text):
    matches = re.findall(r'(\d{3,5})\s?kč', text)

    if matches:
        prices = [int(p) for p in matches if int(p) > 50]
        if prices:
            return min(prices)

    return "neznámá"


# 💰 parsování ceny z telegramu
def parse_price_filter(msg):
    min_price = 0
    max_price = 999999

    match = re.search(r'(\d+)\s*-\s*(\d+)', msg)
    if match:
        min_price = int(match.group(1))
        max_price = int(match.group(2))
        msg = msg.replace(match.group(0), "").strip()
        return msg, min_price, max_price

    match = re.search(r'(\d+)\+', msg)
    if match:
        min_price = int(match.group(1))
        msg = msg.replace(match.group(0), "").strip()
        return msg, min_price, max_price

    return msg, min_price, max_price


# 🔗 URL builder
def build_search_urls(term):
    term = term.replace(" ", "+")

    base_urls = [
        "https://www.vesely-drak.sk/hledani?string={}",
        "https://www.cardstore.cz/search?controller=search&s={}",
        "https://www.gengar.cz/?s={}&post_type=product",
        "https://www.shadowball.cz/?s={}&post_type=product",
        "https://www.pokemall.cz/search?q={}",
        "https://www.pokemon-karty.cz/?s={}&post_type=product",
        "https://www.cardpro.cz/?s={}&post_type=product",
        "https://www.pokemon4u.cz/?s={}&post_type=product",
        "https://www.kuma.cz/?s={}&post_type=product",
        "https://www.alola.cz/?s={}&post_type=product",
        "https://www.pokesov.cz/?s={}&post_type=product",
        "https://www.brloh.cz/?s={}&post_type=product",
        "https://www.cardempire.cz/?s={}&post_type=product",
    ]

    return [url.format(term) for url in base_urls]


# 🔍 kontrola webů
def check_sites():
    global sent_links

    for term, data in search_tasks.items():
        urls = data["urls"]
        min_price = data["min"]
        max_price = data["max"]

        for url in urls:
            try:
                r = requests.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=10,
                    verify=False
                )

                soup = BeautifulSoup(r.text, "html.parser")
                text = soup.get_text().lower()

                if (
                    any(word in text for word in ["skladem", "in stock", "dostupné"])
                    and is_relevant(text, term)
                    and has_product_type(text)
                ):

                    if url not in sent_links:
                        price = get_price(text)

                        if price != "neznámá":
                            if not (min_price <= price <= max_price):
                                print(f"❌ mimo rozsah {price} Kč ({term})")
                                continue

                        send_telegram(f"🔥 RESTOCK ({term})\n{url}\n💸 Cena: {price} Kč")
                        sent_links.add(url)

                else:
                    print(f"není skladem ({term}):", url)

            except Exception as e:
                print("chyba:", e)


# 🤖 start
send_telegram("🤖 Bot běží! Piš co chceš hledat.")


# 🔁 loop
while True:
    try:
        msgs = get_updates()

        for msg in msgs:

            if msg == "stop":
                search_tasks.clear()
                send_telegram("🛑 Všechno zastaveno")

            elif " stop" in msg:
                term = msg.replace(" stop", "").strip()

                if term in search_tasks:
                    del search_tasks[term]
                    send_telegram(f"🛑 Zastaveno: {term}")
                else:
                    send_telegram("❌ Nic takového nehledám")

            else:
                term, min_price, max_price = parse_price_filter(msg)

                if term not in search_tasks:
                    search_tasks[term] = {
                        "urls": build_search_urls(term),
                        "min": min_price,
                        "max": max_price
                    }
                    send_telegram(f"🔍 {term}\n💸 {min_price}-{max_price} Kč")
                else:
                    send_telegram("⚠️ Už hledám")

        if search_tasks:
            check_sites()
        else:
            print("⏸️ nic nehledám...")

        time.sleep(60)

    except Exception as e:
        print("error:", e)
        time.sleep(60)
