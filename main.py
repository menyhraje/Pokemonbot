import requests
from bs4 import BeautifulSoup
import time
import os

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

URLS = [
    "https://www.dracik.cz/pokemon-tcg-sv10-5-black-bolt-white-flare/",
    "https://www.cardempire.sk/pokemon-tcg-white-flare-elite-trainer-box/",
    "https://www.vesely-drak.cz/produkty/pokemon-elite-trainer-box/15769-pokemon-white-flare-elite-trainer-box/",
    "https://www.vesely-drak.cz/produkty/pokemon-elite-trainer-box/15770-pokemon-black-bolt-elite-trainer-box/",
    "https://www.shadowball.cz/pokemon-tcg--scarlet-violet---white-flare-elite-trainer-box/",
    "https://www.shadowball.cz/pokemon-tcg--scarlet-violet---black-bolt-elite-trainer-box/",
    "https://www.cardstore.cz/pokemon-scarlet-and-violet-white-flare-booster-box-japonsky/",
    "https://www.cardstore.cz/pokemon-scarlet-and-violet-black-bolt-booster-box-japonsky/",
    "https://www.smarty.cz/Pokemon-TCG-SV10-5-Black-Bolt-Elite-Trainer-Box-4p231149",
    "https://www.smarty.cz/Pokemon-TCG-SV10-5-White-Flare-Elite-Trainer-Box-4p231148",
]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

def check_site(url):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text().lower()

        if "skladem" in text:
            send_telegram(f"🔥 RESTOCK!\n{url}")
        else:
            print("není:", url)

    except Exception as e:
        print("chyba:", e)

while True:
    for url in URLS:
        check_site(url)

    time.sleep(60)
