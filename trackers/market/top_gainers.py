import requests
from core.state_manager import load_state, save_state
from core.line_notifier import send_line_message

COINGECKO_API = "https://api.coingecko.com/api/v3/coins/markets"

def fetch_top_gainers(vs_currency="usd", per_page=50, page=1):
    params = {
        "vs_currency": vs_currency,
        "order": "market_cap_desc",
        "per_page": per_page,
        "page": page,
        "price_change_percentage": "24h"
    }
    try:
        r = requests.get(COINGECKO_API, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Top Gainers fetch error:", e)
        return []

def check_top_gainers(threshold_pct=20):
    """
    แจ้งเตือนเหรียญที่ +X% ขึ้นไปใน 24h
    threshold_pct = % ขั้นต่ำ เช่น 20 = +20%
    """
    state = load_state()
    seen = set(state.get("market_top_gainers", []))

    coins = fetch_top_gainers()

    for c in coins:
        price_change = c.get("price_change_percentage_24h") or 0
        if price_change < threshold_pct:
            continue

        coin_id = c.get("id")
        symbol = c.get("symbol", "").upper()
        name = c.get("name", "")
        price = c.get("current_price", 0)

        if coin_id in seen:
            continue

        msg = (
            f"[Top Gainer 24h]\n"
            f"{name} ({symbol})\n"
            f"Price: ${price:,.4f}\n"
            f"Change: +{price_change:.1f}%"
        )
        print(msg)
        send_line_message(msg)

        seen.add(coin_id)

    state["market_top_gainers"] = list(seen)
    save_state(state)
