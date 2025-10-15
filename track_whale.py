import os
import requests
import json

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_TARGET_ID = os.getenv("LINE_TARGET_ID", "")  # userId (U...) หรือ groupId (C...)
TARGET_WALLET = os.getenv("WALLET", "").strip()
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")
THRESHOLD_USD = float(os.getenv("THRESHOLD_USD", "100000"))
STATE_FILE = "state.json"

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"
LINE_HEADERS = {
    "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

def send_line_message(text: str):
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_TARGET_ID:
        print("❌ LINE config is missing")
        return
    payload = {"to": LINE_TARGET_ID, "messages": [{"type": "text", "text": text[:4900]}]}
    try:
        res = requests.post(LINE_PUSH_URL, headers=LINE_HEADERS, json=payload, timeout=10)
        print("LINE:", res.status_code, res.text[:200])
    except Exception as e:
        print("❌ LINE send error:", e)

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            return json.load(open(STATE_FILE, "r"))
        except Exception:
            return {}
    return {}

def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def fetch_erc20_transfers(addr: str, apikey: str, limit=20):
    """ดึงธุรกรรม ERC20 ล่าสุดจาก Etherscan"""
    if not apikey:
        return []
    url = (
        "https://api.etherscan.io/api"
        f"?module=account&action=tokentx&address={addr}"
        f"&page=1&offset={limit}&sort=desc&apikey={apikey}"
    )
    try:
        data = requests.get(url, timeout=10).json()
        if data.get("status") != "1":
            return []
        return data.get("result", [])
    except Exception as e:
        print("❌ Etherscan error:", e)
        return []

def detect_large_transfers(transfers):
    """หาธุรกรรมโอน Stablecoin ก้อนใหญ่"""
    alerts = []
    stables = ["USDT", "USDC", "DAI"]

    for tx in transfers:
        symbol = (tx.get("tokenSymbol") or "").upper()
        decimals = int(tx.get("tokenDecimal") or 18)
        value = float(tx.get("value") or 0) / (10 ** decimals)

        if symbol in stables and value >= THRESHOLD_USD:
            tx_hash = tx.get("hash")
            alerts.append(
                f"🔔 Whale Transfer Detected\n"
                f"Token: {symbol}\n"
                f"Amount: {value:,.0f}\n"
                f"Tx: https://etherscan.io/tx/{tx_hash}"
            )
    return alerts

def main():
    if not TARGET_WALLET:
        print("❌ WALLET env not set")
        return

    # ส่งครั้งแรกเท่านั้น (on-chain)
    state = load_state()
    if not state.get("_boot_sent_onchain"):
        send_line_message(
            f"🚀 On-chain tracker started\nWallet: {TARGET_WALLET}\nThreshold: {THRESHOLD_USD:,.0f} USD"
        )
        state["_boot_sent_onchain"] = True
        save_state(state)

    if ETHERSCAN_API_KEY:
        transfers = fetch_erc20_transfers(TARGET_WALLET, ETHERSCAN_API_KEY, limit=20)
        alerts = detect_large_transfers(transfers)
        for msg in alerts:
            send_line_message(msg)

if __name__ == "__main__":
    main()
