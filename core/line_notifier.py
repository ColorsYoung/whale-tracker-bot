import requests
from .config import LINE_CHANNEL_ACCESS_TOKEN, LINE_TARGET_ID

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"
LINE_HEADERS = {
    "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

def send_line_message(text: str) -> None:
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_TARGET_ID:
        print("LINE config is missing")
        return
    payload = {"to": LINE_TARGET_ID, "messages": [{"type": "text", "text": text[:4900]}]}
    try:
        r = requests.post(LINE_PUSH_URL, headers=LINE_HEADERS, json=payload, timeout=12)
        print("LINE:", r.status_code, r.text[:200])
    except Exception as e:
        print("LINE send error:", e)
