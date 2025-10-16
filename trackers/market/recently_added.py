import requests
from core.state_manager import load_state, save_state
from core.line_notifier import send_line_message

COINGECKO_LIST_API = "https://api.coingecko.com/api/v3/coins/list?include_platform=false"

def fetch_all_coins():
    try:
        r = requests.get(COINGECKO_LIST_API, timeout=10)
        r.raise_for_status()
        return r.json()  # list of {id, symbol, name}
    except Exception as e:
        print("Recently Added fetch error:", e)
        return []

def check_recently_added(limit=5):
    """
    ดึงเหรียญใหม่ล่าสุด (ท้าย list)
    แจ้งเตือนเฉพาะเหรียญที่ยังไม่เคยแจ้ง
    """
    state = load_state()
    seen = set(state.get("market_recently_added", []))

    coins = fetch_all_coins()
    if not coins:
        return

    # เอาเหรียญท้าย list (ใหม่สุด)
    new_coins = coins[-50:]  # ป้องกันเยอะเกิน เอา 50 ตัวล่าสุดพอ
    count = 0

    # เดินย้อนจากตัวล่าสุด
    for c in reversed(new_coins):
        coin_id = c.get("id")
        symbol = (c.get("symbol") or "").upper()
        name = c.get("name", "")

        if coin_id in seen:
            continue

        msg = (
            f"[New Coin Added]\n"
            f"{name} ({symbol})\n"
            f"CoinGecko ID: {coin_id}"
        )
        print(msg)
        send_line_message(msg)

        seen.add(coin_id)
        count += 1

        if count >= limit:
            break

    state["market_recently_added"] = list(seen)
    save_state(state)
