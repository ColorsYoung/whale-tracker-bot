import requests
from core.state_manager import load_state, save_state
from core.line_notifier import send_line_message

COINGECKO_TRENDING_API = "https://api.coingecko.com/api/v3/search/trending"

def fetch_trending_coins():
    try:
        r = requests.get(COINGECKO_TRENDING_API, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("coins", [])
    except Exception as e:
        print("Trending fetch error:", e)
        return []

def check_trending_coins(limit=5):
    """
    ดึงเหรียญที่กำลังถูกค้นหาเยอะที่สุดจาก CoinGecko (Top7)
    แจ้งเตือนเฉพาะเหรียญใหม่ที่ยังไม่ถูกแจ้งมาก่อน
    """
    state = load_state()
    seen = set(state.get("market_trending", []))

    coins = fetch_trending_coins()
    count = 0

    for item in coins:
        c = item.get("item", {})
        coin_id = c.get("id")
        symbol = (c.get("symbol") or "").upper()
        name = c.get("name", "")
        rank = c.get("market_cap_rank")
        score = c.get("score")  # อันดับความนิยม (0 = top)

        if not coin_id or coin_id in seen:
            continue

        msg = (
            f"[Trending Coin]\n"
            f"{name} ({symbol})\n"
            f"Market Cap Rank: {rank}\n"
            f"Trending Rank: {score}"
        )
        print(msg)
        send_line_message(msg)

        seen.add(coin_id)
        count += 1
        if count >= limit:
            break

    state["market_trending"] = list(seen)
    save_state(state)
