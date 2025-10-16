import os

# LINE
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
LINE_TARGET_ID = os.getenv("LINE_TARGET_ID", "").strip()

# On-chain / Wallets
TARGET_WALLET = os.getenv("WALLET", "").strip()
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "").strip()
THRESHOLD_USD = float(os.getenv("THRESHOLD_USD", "100000"))

# Hyperliquid thresholds
SIZE_CHANGE_PCT = float(os.getenv("SIZE_CHANGE_PCT", "20"))
PNL_ALERT_PCT = float(os.getenv("PNL_ALERT_PCT", "20"))

# State file
STATE_FILE = os.getenv("STATE_FILE", "state.json")

# Binance CMS API
BINANCE_CMS_API = "https://www.binance.com/bapi/composite/v1/public/cms/article/list"
