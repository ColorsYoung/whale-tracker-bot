# trackers/news/crypto_news.py

import os
import requests
from core.state_manager import load_state, save_state
from core.line_notifier import send_line_message

API_KEY = os.getenv("CRYPTOPANIC_API_KEY", "")
BASE_URL = "https://cryptopanic.com/api/developer/v2/posts/"

# ใช้เฉพาะ filter ที่ Developer Plan รองรับ
FILTERS = ["important", "bullish", "bearish"]

def fetch_news(filter_type: str, size: int = 20):
    if not API_KEY:
        return []

    params = {
        "auth_token": API_KEY,
        "public": "true",
        "kind": "news",
        "filter": filter_type,
        "size": size
    }

    try:
        r = requests.get(BASE_URL, params=params, timeout=10)
        if r.status_code != 200:
            print(f"CryptoPanic {filter_type} status {r.status_code}")
            return []
        data = r.json()
        return data.get("results", [])
    except Exception as e:
        print(f"CryptoPanic exception ({filter_type}):", e)
        return []

def check_crypto_news_all(limit_each=3):
    state = load_state()
    if "seen_crypto_news" not in state:
        state["seen_crypto_news"] = []
    seen = set(state["seen_crypto_news"])

    for ft in FILTERS:
        news_list = fetch_news(ft, size=20)
        if not news_list:
            print(f"⚠️ No data for {ft}")
            continue

        count = 0
        for item in news_list:
            nid = item.get("id")
            if not nid or nid in seen:
                continue

            title = item.get("title", "")
            url = item.get("url") or item.get("original_url") or ""
            when = item.get("published_at", "")

            msg = f"[CryptoPanic {ft.upper()}]\n{title}\nTime: {when}\n{url}"
            print(msg)
            send_line_message(msg)

            seen.add(nid)
            count += 1
            if count >= limit_each:
                break

    state["seen_crypto_news"] = list(seen)
    save_state(state)
