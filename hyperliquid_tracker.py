import os, json, time, requests
from datetime import datetime, timezone

LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_TARGET_ID = os.getenv("LINE_TARGET_ID", "")
WALLET = os.getenv("WALLET", "").strip()

# เกณฑ์แจ้งเตือน (ปรับได้ผ่าน Secrets/Env ใน workflow)
SIZE_CHANGE_PCT = float(os.getenv("SIZE_CHANGE_PCT", "20"))   # เปลี่ยนขนาด >= 20% ให้เตือน
PNL_ALERT_PCT   = float(os.getenv("PNL_ALERT_PCT", "20"))     # PnL ถึง +/-20% ให้เตือน
STATE_FILE = "state.json"

LINE_URL = "https://api.line.me/v2/bot/message/push"
LINE_HEADERS = {"Authorization": f"Bearer {LINE_TOKEN}", "Content-Type": "application/json"}

def send_line(text: str):
    if not LINE_TOKEN or not LINE_TARGET_ID:
        print("❌ Missing LINE envs")
        return
    payload = {"to": LINE_TARGET_ID, "messages": [{"type": "text", "text": text[:4900]}]}
    try:
        r = requests.post(LINE_URL, headers=LINE_HEADERS, json=payload, timeout=10)
        print("LINE:", r.status_code, r.text[:200])
    except Exception as e:
        print("❌ LINE error:", e)

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

def fmt_usd(x: float) -> str:
    try:
        return f"${x:,.0f}"
    except Exception:
        return str(x)

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

def fetch_hyperliquid_positions(address: str):
    """ดึงตำแหน่ง Perp ของ address จาก Hyperliquid (public API)"""
    if not address:
        return []
    urls = [
        f"https://api.hyperliquid.xyz/info/v2/userPositions?address={address}",
        f"https://api.hyperliquid.xyz/info/userPositions?address={address}",
    ]
    for url in urls:
        try:
            res = requests.get(url, timeout=12)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, dict) and "data" in data:
                    data = data["data"]
                if not data:
                    return []
                norm = []
                for p in data:
                    symbol = p.get("symbol") or p.get("asset") or p.get("coin") or "UNKNOWN"
                    side   = (p.get("side") or p.get("positionSide") or "").upper()
                    size   = float(p.get("sizeUsd") or p.get("size") or p.get("value") or 0.0)
                    entry  = float(p.get("entryPrice") or p.get("entryPx") or p.get("avgEntry") or 0.0)
                    liq    = float(p.get("liqPrice") or p.get("liquidation") or 0.0)
                    pnl    = float(p.get("unrealizedPnl") or p.get("uPnl") or 0.0)
                    lev    = float(p.get("leverage") or p.get("lev") or 0.0)
                    norm.append({
                        "symbol": str(symbol),
                        "side": "LONG" if "LONG" in side else ("SHORT" if "SHORT" in side else side),
                        "sizeUsd": size,
                        "entryPrice": entry,
                        "liqPrice": liq,
                        "uPnl": pnl,
                        "leverage": lev
                    })
                return norm
        except Exception as e:
            print("Fetch HL error:", e)
    return []

def compare_and_alert(prev: dict, curr_list: list):
    """
    prev: state เดิมรูปแบบ {symbol: {...}}
    curr_list: รายการ position ปัจจุบัน (list)
    """
    curr = {p["symbol"]: p for p in curr_list}
    alerts = []

    # A) เปิดใหม่ / B) เพิ่ม-ลดขนาด / C) กลับฝั่ง / D) ปิดโพสิชัน / E) PnL ถึงเกณฑ์
    for sym, p in curr.items():
        side = p["side"] or "-"
        size = float(p.get("sizeUsd") or 0.0)
        entry = float(p.get("entryPrice") or 0.0)
        liq = float(p.get("liqPrice") or 0.0)
        pnl = float(p.get("uPnl") or 0.0)
        lev = float(p.get("leverage") or 0.0)

        prev_p = prev.get(sym)
        if prev_p is None or float(prev_p.get("sizeUsd") or 0.0) <= 0:
            # A) เปิดใหม่
            alerts.append(
                f"🐋 Open {side} {sym}\n"
                f"Size: {fmt_usd(size)}  Lev: x{lev:.1f}\n"
                f"Entry: {entry:.2f}  Liq: {liq:.2f}\n"
                f"Time: {now_iso()}"
            )
        else:
            prev_side = prev_p.get("side")
            prev_size = float(prev_p.get("sizeUsd") or 0.0)
            # C) กลับฝั่ง
            if prev_side != side and size > 0:
                alerts.append(
                    f"⚠️ Flip {sym}\n"
                    f"{prev_side} → {side}\n"
                    f"New size: {fmt_usd(size)}  Entry: {entry:.2f}\n"
                    f"Time: {now_iso()}"
                )
            else:
                # B) เปลี่ยนขนาด
                if prev_size > 0:
                    change_pct = abs(size - prev_size) / prev_size * 100
                    if change_pct >= SIZE_CHANGE_PCT:
                        direction = "Increase" if size > prev_size else "Reduce"
                        alerts.append(
                            f"🔄 {direction} {sym} {side}\n"
                            f"{fmt_usd(prev_size)} → {fmt_usd(size)}  ({change_pct:.1f}%)\n"
                            f"Entry: {entry:.2f}  Liq: {liq:.2f}\n"
                            f"Time: {now_iso()}"
                        )
            # E) PnL ถึงเกณฑ์ (ประเมิน % จาก sizeUsd)
            if size > 0:
                pnl_pct = (pnl / size) * 100 if size else 0.0
                if abs(pnl_pct) >= PNL_ALERT_PCT:
                    sign = "✅ Profit" if pnl_pct > 0 else "❌ Loss"
                    alerts.append(
                        f"{sign} on {sym} {side}\n"
                        f"PNL: {fmt_usd(pnl)}  ({pnl_pct:.1f}%)\n"
                        f"Size: {fmt_usd(size)}  Entry: {entry:.2f}\n"
                        f"Time: {now_iso()}"
                    )

    # D) ปิดโพสิชัน
    for sym, prev_p in prev.items():
        if sym not in curr or float(curr.get(sym, {}).get("sizeUsd") or 0.0) <= 0:
            if float(prev_p.get("sizeUsd") or 0.0) > 0:
                alerts.append(
                    f"✅ Close {prev_p.get('side')} {sym}\n"
                    f"Prev size: {fmt_usd(float(prev_p.get('sizeUsd') or 0.0))}\n"
                    f"Time: {now_iso()}"
                )
    return alerts, curr

def main():
    if not WALLET:
        print("❌ WALLET env not set")
        return

    # ส่งครั้งแรกเท่านั้น (บันทึกใน state.json)
    state = load_state()
    if not state.get("_boot_sent_hl"):
        send_line(f"🚀 Hyperliquid tracker started\nWallet: {WALLET}\nTime: {now_iso()}")
        state["_boot_sent_hl"] = True
        save_state(state)

    pos = fetch_hyperliquid_positions(WALLET)
    print("Positions:", pos)

    prev_positions = state.get("positions", {})
    alerts, new_positions = compare_and_alert(prev_positions, pos)

    for msg in alerts:
        send_line(msg)
        time.sleep(0.3)

    state["positions"] = new_positions
    save_state(state)

if __name__ == "__main__":
    main()
