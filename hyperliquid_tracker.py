import os, json, time, requests
from datetime import datetime, timezone

LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_TARGET_ID = os.getenv("LINE_TARGET_ID", "")

# เกณฑ์แจ้งเตือน (ปรับได้ผ่าน Secrets/Env)
SIZE_CHANGE_PCT = float(os.getenv("SIZE_CHANGE_PCT", "20"))   # เปลี่ยนขนาด >= 20% ให้เตือน
PNL_ALERT_PCT   = float(os.getenv("PNL_ALERT_PCT", "20"))     # PnL ถึง +/-20% ให้เตือน
STATE_FILE = "state.json"

# ---- รายชื่อวาฬ (ค่าเริ่มต้น 2 คน) ----
DEFAULT_WALLETS = [
    {"name": "Whale A", "address": "0xb317d2bc2d3d2df5fa441b5bae0ab9d8b07283ae"},
    {"name": "Whale B", "address": "0xf429b2c3f2b7f195367ab6a9b9af279b9d494de5"},
]
# หากต้องการ override ผ่าน ENV ให้ตั้ง WALLETS_JSON เป็น JSON array ของ {name, address}
ENV_WALLETS = os.getenv("WALLETS_JSON", "").strip()
if ENV_WALLETS:
    try:
        DEFAULT_WALLETS = json.loads(ENV_WALLETS)
    except Exception:
        pass

# รองรับ fallback: ถ้ามี WALLET เดี่ยวใน ENV และยังไม่อยู่ในลิสต์ จะเพิ่มเป็น "Primary"
SINGLE_WALLET = os.getenv("WALLET", "").strip()
if SINGLE_WALLET and all(w["address"].lower() != SINGLE_WALLET.lower() for w in DEFAULT_WALLETS):
    DEFAULT_WALLETS = [{"name": "Primary", "address": SINGLE_WALLET}] + DEFAULT_WALLETS

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

def short_addr(addr: str) -> str:
    a = addr.lower()
    return a[:6] + "..." + a[-4:] if len(a) > 10 else a

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

def compare_and_alert(whale_name: str, prev: dict, curr_list: list):
    """
    prev: state เดิมของวาฬนี้ {symbol: {...}}
    curr_list: positions ปัจจุบัน (list)
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
                f"🐋 {whale_name}\n"
                f"OPEN {side} {sym}\n"
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
                    f"⚠️ {whale_name}\n"
                    f"FLIP {sym}: {prev_side} → {side}\n"
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
                            f"🔄 {whale_name}\n"
                            f"{direction} {sym} {side}\n"
                            f"{fmt_usd(prev_size)} → {fmt_usd(size)}  ({change_pct:.1f}%)\n"
                            f"Entry: {entry:.2f}  Liq: {liq:.2f}\n"
                            f"Time: {now_iso()}"
                        )
            # E) PnL ถึงเกณฑ์
            if size > 0:
                pnl_pct = (pnl / size) * 100 if size else 0.0
                if abs(pnl_pct) >= PNL_ALERT_PCT:
                    sign = "✅ Profit" if pnl_pct > 0 else "❌ Loss"
                    alerts.append(
                        f"{sign} • {whale_name}\n"
                        f"{sym} {side} | PNL: {fmt_usd(pnl)} ({pnl_pct:.1f}%)\n"
                        f"Size: {fmt_usd(size)}  Entry: {entry:.2f}\n"
                        f"Time: {now_iso()}"
                    )

    # D) ปิดโพสิชัน (เดิมมี ตอนนี้ไม่มี)
    for sym, prev_p in prev.items():
        if sym not in curr or float(curr.get(sym, {}).get("sizeUsd") or 0.0) <= 0:
            if float(prev_p.get("sizeUsd") or 0.0) > 0:
                alerts.append(
                    f"✅ {whale_name}\n"
                    f"CLOSE {prev_p.get('side')} {sym}\n"
                    f"Prev size: {fmt_usd(float(prev_p.get('sizeUsd') or 0.0))}\n"
                    f"Time: {now_iso()}"
                )
    return alerts, curr

def main():
    wallets = DEFAULT_WALLETS[:]
    if not wallets:
        print("❌ No wallets configured")
        return

    state = load_state()
    # เตรียมช่องเก็บสถานะตามวาฬ
    if "positions" not in state or not isinstance(state["positions"], dict):
        state["positions"] = {}

    for w in wallets:
        name = w["name"]
        addr = w["address"].strip()
        prev = state["positions"].get(name, {})

        # ส่ง “Started” ครั้งแรกต่อวาฬ
        boot_key = f"_boot_sent_hl::{name}"
        if not state.get(boot_key):
            send_line(f"🚀 Hyperliquid tracker started\n{name} • {short_addr(addr)}")
            state[boot_key] = True
            save_state(state)

        pos = fetch_hyperliquid_positions(addr)
        print(f"[{name}] Positions:", pos)

        alerts, new_positions = compare_and_alert(name, prev, pos)
        for msg in alerts:
            send_line(msg)
            time.sleep(0.3)

        state["positions"][name] = new_positions
        save_state(state)

if __name__ == "__main__":
    main()
