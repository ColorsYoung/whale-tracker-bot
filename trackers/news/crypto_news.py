# trackers/news/crypto_news.py
import os
import requests
from datetime import datetime
from core.line_notifier import send_line_message
from core.state_manager import load_state, save_state

API_KEY = os.getenv("CRYPTOPANIC_API_KEY", "")
API_URL = "https://cryptopanic.com/api/developer/v2/posts/"

# ✅ คีย์เวิร์ดที่สื่อถึง “ข่าวมีผลต่อราคา”
IMPACT_KEYWORDS = [
    "binance", "listing", "hack", "partnership", "launch",
    "upgrade", "airdrop", "invest", "regulation", "lawsuit",
    "exploit", "adoption", "sec", "etf", "delist",
]

def _contains_impact(text: str) -> bool:
    text = text.lower()
    return any(k in text for k in IMPACT_KEYWORDS)

def _fmt_time(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return iso

def fetch_news(size=20):
    if not API_KEY:
        print("❌ No CRYPTOPANIC_API_KEY")
        return []

    params = {
        "auth_token": API_KEY,
        "public": "true",    # ✅ ใช้ public mode
        "kind": "news",
        "size": size         # ✅ Developer plan max 20
    }

    try:
        r = requests.get(API_URL, params=params, timeout=15)
        if r.status_code == 500:
            print("CryptoPanic 500 error")
            return []
        r.raise_for_status()
        data = r.json()
        return data.get("results", [])
    except Exception as e:
        print("CryptoPanic fetch error:", e)
        return []

def check_crypto_news(limit=5):
    state = load_state()
    seen_ids = set(state.get("crypto_news_ids", []))

    news_list = fetch_news(size=20)
    if not news_list:
        return

    count = 0
    for item in news_list:
        nid = item.get("id")
        if nid in seen_ids:
            continue

        title = item.get("title", "")
        desc = item.get("description", "") or ""
        if not _contains_impact(title + " " + desc):
            continue  # ✅ กรองเฉพาะข่าวสำคัญ

        pub_time = _fmt_time(item.get("published_at", ""))
        link = item.get("url") or item.get("original_url") or ""

        msg = (
            f"[Crypto News]\n"
            f"{title}\n"
            f"Time: {pub_time}\n"
            f"{link}"
        )
        print(msg)
        send_line_message(msg)

        seen_ids.add(nid)
        count += 1
        if count >= limit:
            break

    state["crypto_news_ids"] = list(seen_ids)
    save_state(state)
