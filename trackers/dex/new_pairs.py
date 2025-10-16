import requests
from core.state_manager import load_state, save_state
from core.line_notifier import send_line_message

DEX_API = "https://api.dexscreener.com/latest/dex/search"

CHAINS = ["ethereum", "bsc", "arbitrum", "base", "solana"]


def check_new_dex_pairs(liq_threshold=50000, limit=5):
    state = load_state()
    seen = set(state.get("dex_pairs_seen", []))

    for chain in CHAINS:
        try:
            resp = requests.get(DEX_API, params={"q": chain}, timeout=10)
            resp.raise_for_status()
            data = resp.json().get("pairs", [])
        except Exception as e:
            print(f"DEX fetch error ({chain}):", e)
            continue

        for pair in data[:limit]:
            pair_id = pair.get("pairAddress")
            if pair_id in seen:
                continue

            liquidity = pair.get("liquidity", {}).get("usd", 0)
            if liquidity < liq_threshold:
                continue

            base = pair.get("baseToken", {}).get("symbol", "")
            quote = pair.get("quoteToken", {}).get("symbol", "")
            price = pair.get("priceUsd", "?")
            url = pair.get("url", "")

            msg = (
                f"[DEX New Pair] {base}/{quote}\n"
                f"Chain: {chain}\n"
                f"Liq: ${liquidity:,.0f}\n"
                f"Price: {price}\n"
                f"{url}"
            )
            print(msg)
            send_line_message(msg)

            seen.add(pair_id)

    state["dex_pairs_seen"] = list(seen)
    save_state(state)
