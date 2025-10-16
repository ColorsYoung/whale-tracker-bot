import requests
from datetime import datetime
from track_whale import send_line_message, load_state, save_state

# Binance CMS API (ลับแต่ใช้ได้จริง)
API_URL = "https://www.binance.com/bapi/composite/v1/public/cms/article/list"

def fetch_binance_announcements():
    """
    ดึงประกาศจาก Binance (เฉพาะหมวด Listing catalogId=48)
    """
    params = {
        "type": 1,
        "catalogId": 48,     # 48 = หมวดประกาศลิสต์เหรียญใหม่
        "pageNo": 1,
        "pageSize": 20
    }
    try:
        res = requests.get(API_URL, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        return data.get("data", {}).get("articles", [])
    except Exception as e:
        print("❌ Error fetching Binance announcements:", e)
        return []

def is_listing_announcement(title: str) -> bool:
    """
    กรองเฉพาะประกาศที่หมายถึง 'ลิสต์เหรียญใหม่'
    """
    keywords = ["Will List", "Lists", "Launchpool", "Launchpad", "Trading Opens"]
    return any(kw in title for kw in keywords)

def check_binance_listing():
    """
    1. ดึงประกาศล่าสุด
    2. กรองเฉพาะที่ลิสต์เหรียญ
    3. กันแจ้งซ้ำด้วย state.json
    4. ส่ง LINE ทันที
    """
    state = load_state()
    if "binance_announced" not in state:
        state["binance_announced"] = []

    seen_titles = state["binance_announced"]
    articles = fetch_binance_announcements()
    if not articles:
        return

    for a in articles:
        title = a.get("title", "")
        if not is_listing_announcement(title):
            continue
        
        if title in seen_titles:
            continue  # แจ้งไปแล้ว ข้าม

        ts = a.get("releaseDate", 0)
        date_str = datetime.fromtimestamp(ts/1000).strftime("%Y-%m-%d %H:%M")

        link = "https://www.binance.com/en/support/announcement/" + str(a.get("id", ""))

        message = f"🚨 NEW BINANCE LISTING!\n{title}\nTime: {date_str}\n{link}"
        print(message)

        try:
            send_line_message(message)
        except Exception as e:
            print("❌ Failed to send LINE message:", e)

        seen_titles.append(title)

    state["binance_announced"] = seen_titles
    save_state(state)

if __name__ == "__main__":
    check_binance_listing()
