# binance_pairs.py
import re
from datetime import datetime
import requests

# reuse ของเดิมจากโปรเจกต์คุณ
from track_whale import send_line_message, load_state, save_state

API_URL = "https://www.binance.com/bapi/composite/v1/public/cms/article/list"

# -------------------------
# ตัวช่วย
# -------------------------
def _fetch_articles():
    """
    ดึงประกาศล่าสุดจาก Binance (หมวด Listing/Pairs/Margin/Futures: catalogId=48)
    """
    params = {
        "type": 1,
        "catalogId": 48,   # ประกาศลิสต์/คู่เทรด/มาร์จิ้น/ฟิวเจอร์ส มักอยู่หมวดนี้
        "pageNo": 1,
        "pageSize": 20
    }
    try:
        r = requests.get(API_URL, params=params, timeout=10)
        r.raise_for_status()
        return (r.json().get("data") or {}).get("articles", [])
    except Exception as e:
        print("❌ Fetch Binance pairs error:", e)
        return []

def _is_futures(title: str) -> bool:
    """จับ Futures/Perpetual"""
    title = title or ""
    keys = [
        "Futures Will Launch",
        "Will Launch",
        "Perpetual Contract",
        "USDT-M Perpetual",
        "USDⓈ-M Perpetual",
        "Coin-M Perpetual",
    ]
    return any(k in title for k in keys)

def _is_margin(title: str) -> bool:
    """จับ Margin (Isolated/Cross/borrow/list)"""
    title = title or ""
    keys = [
        "Isolated Margin",
        "Cross Margin",
        "Margin Pairs",
        "Margin Trading",
        "Added to Margin",
        "Adds the following assets and pairs on Margin",
    ]
    return any(k in title for k in keys)

def _is_spot_pairs(title: str) -> bool:
    """จับ Spot trading pairs ใหม่ (ไม่ใช่ลิสต์เหรียญใหม่)"""
    title = title or ""
    # keywords ที่พบบ่อย: Adds XXX/YYY, Will Add XXX/YYY, Adds Trading Pairs
    keys = [
        "Adds Trading Pairs",
        "Will Add Trading Pairs",
        "Adds the following trading pairs",
        "Adds",
        "Will Add",
    ]
    # กันชนกับประกาศ "Will List" (อันนั้นเป็นลิสต์เหรียญใหม่ ซึ่งคุณทำไว้ใน binance_listing.py แล้ว)
    if "Will List" in title:
        return False
    return any(k in title for k in keys) and bool(re.search(r"[A-Z0-9]{2,}/[A-Z]{2,5}", title))

def _fmt_dt(ms: int) -> str:
    try:
        return datetime.fromtimestamp(ms/1000).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "-"

# -------------------------
# แจ้งเตือนรวม
# -------------------------
def check_binance_pairs():
    """
    - ตรวจจับ 3 หมวด: Spot pairs / Margin pairs / Futures contracts
    - กันแจ้งซ้ำแยกตามหมวดด้วย state.json
    """
    state = load_state()
    state.setdefault("binance_pairs_spot", [])
    state.setdefault("binance_pairs_margin", [])
    state.setdefault("binance_pairs_futures", [])

    seen_spot   = set(state["binance_pairs_spot"])
    seen_margin = set(state["binance_pairs_margin"])
    seen_future = set(state["binance_pairs_futures"])

    articles = _fetch_articles()
#     articles = [
#     {"id": "test1", "title": "Binance Will List TEST (TEST/USDT)", "releaseDate": 1730000000000},
# ]
    if not articles:
        return

    # เดินจากใหม่ไปเก่า
    for a in articles:
        aid   = str(a.get("id", ""))
        title = a.get("title", "") or ""
        ts    = int(a.get("releaseDate", 0))
        when  = _fmt_dt(ts)
        link  = "https://www.binance.com/en/support/announcement/" + aid

        try:
            if _is_futures(title):
                if aid not in seen_future:
                    msg = f"⚡ Binance Futures: {title}\nTime: {when}\n{link}"
                    print(msg)
                    send_line_message(msg)
                    seen_future.add(aid)

            elif _is_margin(title):
                if aid not in seen_margin:
                    msg = f"🧮 Binance Margin: {title}\nTime: {when}\n{link}"
                    print(msg)
                    send_line_message(msg)
                    seen_margin.add(aid)

            elif _is_spot_pairs(title):
                if aid not in seen_spot:
                    msg = f"🟢 New Spot Pairs: {title}\nTime: {when}\n{link}"
                    print(msg)
                    send_line_message(msg)
                    seen_spot.add(aid)

        except Exception as e:
            print("❌ send_line_message error:", e)

    # save
    state["binance_pairs_spot"]   = list(seen_spot)
    state["binance_pairs_margin"] = list(seen_margin)
    state["binance_pairs_futures"] = list(seen_future)
    save_state(state)

if __name__ == "__main__":
    check_binance_pairs()
