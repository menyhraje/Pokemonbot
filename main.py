import requests
from bs4 import BeautifulSoup
import time
import os
import re

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# 🔍 aktivní hledání
search_tasks = {}  # {"white flare": [urls]}
sent_links = set()
last_update_id = None


# 📩 Telegram
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
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


# 🔗 generování URL
def build_search_urls(term):
    term = term.replace(" ", "+")

    base_urls = [
        "https://www.vesely-drak.cz/hledani?string={}",
        "https://www.vesely-drak.sk/hledani?string={}",
        "https://www.cardstore.cz/search?controller=search&s={}",
        "https://www.gengar.cz/?s={}&post_type=product",
        "https://www.shadowball.cz/?s={}&post_type=product",
        "https://www.pokemall.cz/search?q={}",
        "https://www.pokemon-karty.cz/?s={}&post_type=product",
        "https://www.cardpro.cz/?s={}&post_type=product",
        "https://www.babuobchod.cz/?s={}&post_type=product",
        "https://www.pokemon4u.cz/?s={}&post_type=product",
        "https://www.kuma.cz/?s={}&post_type=product",
        "https://www.alola.cz/?s={}&post_type=product",
        "https://www.pokesov.cz/?s={}&post_type=product",
        "https://www.cardyx.cz/?s={}&post_type=product",
        "https://www.pokecenter.cz/?s={}&post_type=product",
        "https://www.brloh.cz/?s={}&post_type=product",
        "https://www.cardempire.cz/?s={}&post_type=product",
        "https://www.ccplanet.cz/?s={}&post_type=product"
    ]

    return [url.format(term) for url in base_urls]


# 💸 cena
def get_price(text):
    matches = re.findall(r'(\d{3,5})\s?kč', text)

    if matches:
        prices = [int(p) for p in matches if int(p) > 50]
        if prices:
            return min(prices)

    return "neznámá"


# 🔍 kontrola
def check_sites():
    global sent_links

    for term, urls in search_tasks.items():
        for url in urls:
            try:
                r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(r.text, "html.parser")
                text = soup.get_text().lower()

                if any(word in text for word in ["skladem", "in stock", "dostupné"]):

                    if url not in sent_links:
                        price = get_price(text)

                        send_telegram(f"🔥 RESTOCK ({term})\n{url}\n💸 Cena: {price} Kč")

                        sent_links.add(url)

                else:
                    print(f"není skladem ({term}):", url)

            except Exception as e:
                print("chyba:", e)


# 🤖 START
send_telegram("🤖 Bot běží! Piš co chceš hledat.")


# 🔁 MAIN LOOP
while True:
    try:
        msg = get_updates()

        if msg:

            # 🛑 STOP VŠE
            if msg == "stop":
                search_tasks.clear()
                send_telegram("🛑 Všechno hledání zastaveno")

            # 🛑 STOP KONKRÉTNÍ
            elif " stop" in msg:
                term = msg.replace(" stop", "").strip()

                if term in search_tasks:
                    del search_tasks[term]
                    send_telegram(f"🛑 Zastaveno: {term}")
                else:
                    send_telegram("❌ Nic takového nehledám")

            # ➕ NOVÉ HLEDÁNÍ
            else:
                term = msg.strip()

                if term not in search_tasks:
                    search_tasks[term] = build_search_urls(term)
                    send_telegram(f"🔍 Přidáno: {term}")
                else:
                    send_telegram("⚠️ Už hledám")

        # 🔍 běh
        if search_tasks:
            check_sites()
        else:
            print("⏸️ nic nehledám...")

        time.sleep(60)

    except Exception as e:
        print("error:", e)
        time.sleep(60)
