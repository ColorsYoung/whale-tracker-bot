import os
import time
import requests
from core.state_manager import load_state, save_state
from core.line_notifier import send_line_message

API_KEY = os.getenv("CRYPTOPANIC_API_KEY", "")
BASE_URL = "https://cryptopanic.com/api/developer/v2/posts/"


def fetch_news(filter_type="important", limit=20):
    if not API_KEY:
        return []

    params = {
        "auth_token": API_KEY,
        "public": "true",
        "kind": "news",
        "filter": filter_type,
        "size": limit
    }

    try:
        resp = requests.get(BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json().get("results", [])
    except Exception as e:
        print(f"CryptoPanic fetch error ({filter_type}):", e)
        return []


def check_crypto_news_all(limit_each=3):
    categories = ["important", "bullish"]  # ลดเหลือ 2 หมวดก่อน (ปลอดภัย)
    state = load_state()

    for cat in categories:
        key = f"news_{cat}"
        seen = set(state.get(key, []))

        items = fetch_news(cat, limit_each)
        for item in items:
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
                f"[NEWS {cat.upper()}]\n"
                f"{title}\n"
                f"👍{pos} 👎{neg} ⭐{imp}\n"
                f"{url}"
            )
            print(msg)
            send_line_message(msg)
            seen.add(nid)

        state[key] = list(seen)
        save_state(state)

        time.sleep(1.2)  # ป้องกัน rate limit
