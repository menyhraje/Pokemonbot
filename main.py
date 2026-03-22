import requests
from bs4 import BeautifulSoup
import time
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "TVŮJ_TOKEN"

watchlist = {}
last_seen = {}

SEARCH_URLS = [
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
    "https://www.ccplanet.cz/?s={}&post_type=product",
]

def check_product(product_name):
    results = []

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for url in SEARCH_URLS:
        try:
            search_url = url.format(product_name.replace(" ", "+"))
            response = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            items = soup.select("div.product, div.product-item, li.product")

            for item in items:
                text = item.get_text(" ", strip=True).lower()

                if product_name.lower() not in text:
                    continue

                if not is_in_stock(text):
                    continue

                a = item.find("a")
                link = a["href"] if a else search_url

                price_tag = item.select_one(".price, .amount")
                price = price_tag.text.strip() if price_tag else "N/A"

                results.append({
                    "name": product_name,
                    "price": price,
                    "link": link
                })

        except Exception as e:
            print("Error:", e)

    return results


def watcher(chat_id, context):
    while True:
        for product in list(watchlist.get(chat_id, [])):
            results = check_product(product)

            if product not in last_seen:
                last_seen[product] = {}

            for r in results:
                link = r["link"]
                price = r["price"]

                # nikdy neviděno → pošli
                if link not in last_seen[product]:
                    last_seen[product][link] = price

                    message = f"""
🔥 NALEZENO 🔥
Produkt: {r['name']}
Cena: {price}
Odkaz: {link}
"""
                    context.bot.send_message(chat_id=chat_id, text=message)

                # změna ceny → pošli update
                elif last_seen[product][link] != price:
                    old_price = last_seen[product][link]
                    last_seen[product][link] = price

                    message = f"""
🔄 ZMĚNA CENY 🔄
Produkt: {r['name']}
Stará cena: {old_price}
Nová cena: {price}
Odkaz: {link}
"""
                    context.bot.send_message(chat_id=chat_id, text=message)

        time.sleep(30)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    chat_id = update.message.chat_id

    if chat_id not in watchlist:
        watchlist[chat_id] = []

        thread = threading.Thread(target=watcher, args=(chat_id, context))
        thread.daemon = True
        thread.start()

    if text == "stop":
        watchlist[chat_id] = []
        await update.message.reply_text("🛑 Všechno zastaveno")
        return

    if "stop" in text:
        product = text.replace("stop", "").strip()

        if product in watchlist[chat_id]:
            watchlist[chat_id].remove(product)
            await update.message.reply_text(f"🛑 Zastaveno: {product}")
        return

    if text not in watchlist[chat_id]:
        watchlist[chat_id].append(text)
        await update.message.reply_text(f"👀 Sleduju: {text}")
    else:
        await update.message.reply_text("⚠️ Už sleduju")


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot běží...")
    app.run_polling()
