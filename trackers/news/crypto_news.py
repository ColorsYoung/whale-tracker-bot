import os
import time
import requests
from core.state_manager import load_state, save_state
from core.line_notifier import send_line_message

API_KEY = os.getenv("CRYPTOPANIC_API_KEY", "")
BASE_URL = "https://cryptopanic.com/api/developer/v2/posts/"


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


def fetch_news(filter_type="important", limit=10):
    if not API_KEY:
        print("❌ Missing CRYPTOPANIC_API_KEY")
        return []
    params = {
        "auth_token": API_KEY,
        "public": "true",
        "kind": "news",
        "filter": filter_type,
        "size": limit
    }
    return safe_request(params)


def check_crypto_news_all(limit_each=3):
    filters = ["important", "bullish"]
    state = load_state()

    for f in filters:
        seen_key = f"cryptopanic_seen_{f}"
        seen = set(state.get(seen_key, []))
        news = fetch_news(f, limit_each)

        if not news:
            print(f"⚠️ No data for {f}")
            continue

        for item in news:
            nid = str(item.get("id"))
            if nid in seen:
                continue

            title = item.get("title", "")
            url = item.get("url", "")
            votes = item.get("votes", {})
            pos = votes.get("positive", 0)
            neg = votes.get("negative", 0)
            imp = votes.get("important", 0)

            msg = (
                f"[CryptoPanic • {f.upper()}]\n"
                f"{title}\n"
                f"👍 {pos}  👎 {neg}  ⭐ {imp}\n"
                f"{url}"
            )
            print(msg)
            send_line_message(msg)
            seen.add(nid)
            time.sleep(0.8)

        state[seen_key] = list(seen)
        save_state(state)
        time.sleep(2)
