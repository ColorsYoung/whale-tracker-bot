import os
import requests
from core.state_manager import load_state, save_state
from core.line_notifier import send_line_message

API_KEY = os.getenv("CRYPTOPANIC_API_KEY", "")
BASE_URL = "https://cryptopanic.com/api/developer/v2/posts/"

FILTERS = [
    ("important", "[News: Important]"),
    ("bullish",   "[News: Bullish]"),
    ("bearish",   "[News: Bearish]"),
    ("rising",    "[News: Rising]"),
]

def fetch_news(filter_type="important", size=50):
    params = {
        "auth_token": API_KEY,
        "public": "true",
        "kind": "news",
        "filter": filter_type,
        "size": size
    }
    try:
        r = requests.get(BASE_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("results", [])
    except Exception as e:
        print(f"CryptoPanic fetch error ({filter_type}):", e)
        return []

def check_crypto_news_all(limit_each=3):
    """
    ดึงข่าวจากหลาย filter (important, bullish, bearish, rising)
    - limit_each: จำนวนข่าวสูงสุดต่อประเภท
    - ใช้ state กันแจ้งซ้ำ (แยก per ID)
    """
    state = load_state()
    seen = set(state.get("crypto_news_ids", []))

    for filter_type, prefix in FILTERS:
        news_list = fetch_news(filter_type=filter_type, size=50)
        count = 0

        for n in news_list:
            nid = n.get("id")
            title = n.get("title", "")
            url = n.get("url") or n.get("original_url") or ""

            if nid in seen:
                continue

            votes = n.get("votes", {})
            pos = votes.get("positive", 0)
            neg = votes.get("negative", 0)
            imp = votes.get("important", 0)

            panic_score = n.get("panic_score", None)
            panic_text = f"Panic Score: {panic_score}" if panic_score is not None else ""

            msg = (
                f"{prefix}\n"
                f"{title}\n"
                f"👍 {pos} | 👎 {neg} | ⭐ {imp}\n"
                f"{panic_text}\n"
                f"{url}"
            ).strip()

            print(msg)
            send_line_message(msg)

            seen.add(nid)
            count += 1
            if count >= limit_each:
                break

    state["crypto_news_ids"] = list(seen)
    save_state(state)
