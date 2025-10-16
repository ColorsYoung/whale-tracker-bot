# trackers/news/crypto_news.py
import os
import time
import requests
from core.state_manager import load_state, save_state
from core.line_notifier import send_line_message

API_KEY = os.getenv("CRYPTOPANIC_API_KEY", "")
BASE_URL = "https://cryptopanic.com/api/developer/v2/posts/"

# คีย์เวิร์ดที่เราสนใจ
KEYWORDS = [
    "binance", "list", "listing", "launch", "launchpad", "launchpool",
    "hack", "exploit", "etf", "sec", "approval", "pump", "moon",
    "bullish", "bearish"
]


def safe_request(params, retries=3, delay=2):
    for _ in range(retries):
        try:
            resp = requests.get(BASE_URL, params=params, timeout=10)
            if resp.status_code == 200:
                return resp.json().get("results", [])
            else:
                print(f"CryptoPanic status {resp.status_code}")
        except Exception as e:
            print("CryptoPanic request error:", e)
        time.sleep(delay)
    return []


def fetch_news(limit=20):
    if not API_KEY:
        print("❌ Missing CRYPTOPANIC_API_KEY")
        return []
    params = {
        "auth_token": API_KEY,
        "public": "true",
        "kind": "news",
        "size": limit
    }
    return safe_request(params)


def is_relevant_news(title: str, desc: str):
    text = (title or "" + " " + desc or "").lower()
    return any(kw in text for kw in KEYWORDS)


def check_crypto_news(limit=20):
    state = load_state()
    seen = set(state.get("cryptopanic_seen", []))

    news_list = fetch_news(limit)
    if not news_list:
        print("⚠️ No news data")
        return

    for item in news_list:
        nid = str(item.get("id"))
        if nid in seen:
            continue

        title = item.get("title", "")
        desc = item.get("description", "")
        url = item.get("url", "")

        if not is_relevant_news(title, desc):
            continue

        votes = item.get("votes", {})
        pos = votes.get("positive", 0)
        neg = votes.get("negative", 0)
        imp = votes.get("important", 0)

        msg = (
            f"[Crypto News]\n"
            f"{title}\n"
            f"👍 {pos}  👎 {neg}  ⭐ {imp}\n"
            f"{url}"
        )
        print(msg)
        send_line_message(msg)

        seen.add(nid)
        time.sleep(0.8)

    state["cryptopanic_seen"] = list(seen)
    save_state(state)
