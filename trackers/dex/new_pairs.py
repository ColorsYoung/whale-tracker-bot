import requests
from core.state_manager import load_state, save_state
from core.line_notifier import send_line_message

# DexScreener New Pairs API
DEXSCREENER_NEW_PAIRS = "https://api.dexscreener.com/latest/dex/pairs/{}"

# เลือก chain ที่ต้องการติดตาม
CHAINS = ["ethereum", "bsc", "arbitrum", "base", "solana"]

def fetch_new_pairs(chain):
    try:
        url = DEXSCREENER_NEW_PAIRS.format(chain)
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        # {"pairs": [...]}
        return data.get("pairs", [])
    except Exception as e:
        print(f"DEX fetch error ({chain}):", e)
        return []

def check_new_dex_pairs(liq_threshold=50000, limit=5):
    """
    ติดตามคู่เทรดใหม่บน DEX หลาย chain
    - แจ้งเฉพาะคู่ที่มี liquidity >= liq_threshold USD (กันขยะ)
    - ส่ง alert เฉพาะคู่ที่ยังไม่เคยแจ้ง
    """
    state = load_state()
    seen = set(state.get("dex_new_pairs", []))
    count = 0

    for chain in CHAINS:
        pairs = fetch_new_pairs(chain)
        for p in pairs:
            pair_id = p.get("pairAddress")
            base_symbol = p.get("baseToken", {}).get("symbol", "")
            quote_symbol = p.get("quoteToken", {}).get("symbol", "")
            liquidity = p.get("liquidity", {}).get("usd", 0)

            if not pair_id or pair_id in seen:
                continue
            if liquidity < liq_threshold:
                continue  # ตัดขยะ

            name = f"{base_symbol}/{quote_symbol}"
            price = p.get("priceUsd")

            msg = (
                f"[New DEX Pair]\n"
                f"Chain: {chain}\n"
                f"Pair: {name}\n"
                f"Price: ${price}\n"
                f"Liquidity: ${liquidity:,.0f}\n"
                f"Chart: https://dexscreener.com/{chain}/{pair_id}"
            )
            print(msg)
            send_line_message(msg)

            seen.add(pair_id)
            count += 1
            if count >= limit:
                state["dex_new_pairs"] = list(seen)
                save_state(state)
                return

    state["dex_new_pairs"] = list(seen)
    save_state(state)
