import requests
from core.config import TARGET_WALLET, ETHERSCAN_API_KEY, THRESHOLD_USD
from core.line_notifier import send_line_message
from core.state_manager import load_state, save_state

def fetch_erc20_transfers(addr: str, apikey: str, limit=20):
    if not apikey:
        return []
    url = (
        "https://api.etherscan.io/api"
        f"?module=account&action=tokentx&address={addr}"
        f"&page=1&offset={limit}&sort=desc&apikey={apikey}"
    )
    try:
        data = requests.get(url, timeout=12).json()
        if data.get("status") != "1":
            return []
        return data.get("result", [])
    except Exception as e:
        print("Etherscan error:", e)
        return []

def detect_large_transfers(transfers):
    alerts = []
    stables = ["USDT", "USDC", "DAI"]
    for tx in transfers:
        symbol = (tx.get("tokenSymbol") or "").upper()
        decimals = int(tx.get("tokenDecimal") or 18)
        value = float(tx.get("value") or 0) / (10 ** decimals)
        if symbol in stables and value >= THRESHOLD_USD:
            tx_hash = tx.get("hash")
            alerts.append(
                "[Whale Transfer]\n"
                f"Token: {symbol}\n"
                f"Amount: {value:,.0f}\n"
                f"Tx: https://etherscan.io/tx/{tx_hash}"
            )
    return alerts

def run_onchain_tracker():
    if not TARGET_WALLET:
        print("WALLET env not set")
        return

    state = load_state()
    if not state.get("_boot_sent_onchain"):
        send_line_message(
            "[On-chain Tracker Started]\n"
            f"Wallet: {TARGET_WALLET}\n"
            f"Threshold: {THRESHOLD_USD:,.0f} USD"
        )
        state["_boot_sent_onchain"] = True
        save_state(state)

    if ETHERSCAN_API_KEY:
        transfers = fetch_erc20_transfers(TARGET_WALLET, ETHERSCAN_API_KEY, limit=20)
        for msg in detect_large_transfers(transfers):
            send_line_message(msg)
