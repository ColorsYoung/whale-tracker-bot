import os
import requests
from core.state_manager import load_state, save_state
from core.line_notifier import send_line_message

# อ่าน API KEY จาก ENV (หากไม่ตั้ง ENV จะ fallback เป็น key ที่คุณให้)
API_KEY = os.getenv("CRYPTOPANIC_API_KEY", "4739bd824fdeeab738ef5348cbfa0b2038ccca60")

BASE_URL = "https://cryptopanic.com/api/developer/v2/posts/"

def fetch_news(filter_type="important", size=50):
    """
    ดึงข่าวจาก CryptoPanic (Developer API)
    filter_type: important, bullish, bearish, rising, hot, lol ฯลฯ
    size: จำนวนข่าวต่อหน้า (สูงสุด 500)
    """
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
        print("CryptoPanic fetch error:", e)
        return []

def check_crypto_news(filter_type="important", limit=5):
    """
    แจ้งเตือนข่าวสำคัญจาก CryptoPanic
    - filter_type = important (ค่าเริ่มต้น)
    - limit = จำนวนข่าวสูงสุดที่จะส่งแจ้งเตือนในรอบนี้
    - กันแจ้งซ้ำด้วย state
    """
    state = load_state()
    seen = set(state.get("crypto_news_ids", []))
    count = 0

    news_list = fetch_news(filter_type=filter_type, size=50)
    if not news_list:
        return

    for n in news_list:
        nid = n.get("id")
        title = n.get("title", "")
        url = n.get("url") or n.get("original_url") or ""

        if nid in seen:
            continue

        votes = n.get("votes", {})
        positive = votes.get("positive", 0)
        negative = votes.get("negative", 0)
        important = votes.get("important", 0)

        panic_score = n.get("panic_score", None)
        panic_text = f"Panic Score: {panic_score}" if panic_score is not None else ""

        msg = (
            f"[Crypto News - {filter_type}]\n"
            f"{title}\n"
            f"👍 {positive} | 👎 {negative} | ⭐ {important}\n"
            f"{panic_text}\n"
            f"{url}"
        ).strip()

        print(msg)
        send_line_message(msg)

        seen.add(nid)
        count += 1
        if count >= limit:
            break

    state["crypto_news_ids"] = list(seen)
    save_state(state)
