import os
import requests
from core.state_manager import load_state, save_state
from core.line_notifier import send_line_message
from core.config import THRESHOLD_USD

TARGET_WALLET = os.getenv("WALLET", "").strip()
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "").strip()
STATE_KEY = "_boot_sent_onchain"


def run_onchain_tracker():
    """
    ติดตามธุรกรรม Stablecoin ก้อนใหญ่จากวอลเล็ตเป้าหมาย (USDT/USDC/DAI)
    หากไม่มี ETHERSCAN_API_KEY จะข้ามโดยไม่ error
    """
    # ถ้าไม่มี wallet → จบ
    if not TARGET_WALLET:
        print("Skip on-chain tracker (no WALLET)")
        return

    # ถ้าไม่มี API KEY → ข้ามนุ่มนวล
    if not ETHERSCAN_API_KEY:
        print("Skip on-chain tracker (no ETHERSCAN_API_KEY)")
        return

    state = load_state()

    # แจ้งเริ่มครั้งแรก
    if not state.get(STATE_KEY):
        send_line_message(
            f"[On-chain Tracker Started]\n"
            f"Wallet: {TARGET_WALLET}\n"
            f"Threshold: ${THRESHOLD_USD:,.0f}"
        )
        state[STATE_KEY] = True
        save_state(state)

    # ดึงธุรกรรม ERC20
    txs = fetch_erc20_transfers(TARGET_WALLET, ETHERSCAN_API_KEY)
    alerts = detect_large_stable_transfers(txs)

    for msg in alerts:
        send_line_message(msg)


def fetch_erc20_transfers(address: str, apikey: str, limit=20):
    """
    ดึงธุรกรรม ERC20 ล่าสุดจาก Etherscan
    """
    if not apikey:
        return []

    url = (
        "https://api.etherscan.io/api"
        f"?module=account&action=tokentx&address={address}"
        f"&page=1&offset={limit}&sort=desc&apikey={apikey}"
    )
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get("status") != "1":
            return []
        return data.get("result", [])
    except Exception as e:
        print("Etherscan error:", e)
        return []


def detect_large_stable_transfers(transfers):
    """
    หาธุรกรรม stablecoin (USDT/USDC/DAI) ที่มูลค่า >= THRESHOLD_USD
    """
    alerts = []
    stables = ["USDT", "USDC", "DAI"]

    for tx in transfers:
        symbol = (tx.get("tokenSymbol") or "").upper()
        decimals = int(tx.get("tokenDecimal") or 18)
        value = float(tx.get("value") or 0) / (10 ** decimals)

        if symbol in stables and value >= THRESHOLD_USD:
            tx_hash = tx.get("hash")
            alerts.append(
                f"[Whale Transfer]\n"
                f"Token: {symbol}\n"
                f"Amount: {value:,.0f}\n"
                f"Tx: https://etherscan.io/tx/{tx_hash}"
            )
    return alerts
