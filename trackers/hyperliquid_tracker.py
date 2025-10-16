import json
import time
import requests
from datetime import datetime, timezone

from core.line_notifier import send_line_message
from core.state_manager import load_state, save_state
from core.config import SIZE_CHANGE_PCT, PNL_ALERT_PCT

# รายชื่อวาฬเริ่มต้น (override ได้ด้วย ENV WALLETS_JSON หรือ WALLET เดี่ยว ผ่าน main.py ถ้าต้องการ)
DEFAULT_WALLETS = [
    {"name": "Whale A", "address": "0xb317d2bc2d3d2df5fa441b5bae0ab9d8b07283ae"},
    {"name": "Whale B", "address": "0xf429b2c3f2b7f195367ab6a9b9af279b9d494de5"},
]

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

def fmt_usd(x: float) -> str:
    try:
        return f"${x:,.0f}"
    except Exception:
        return str(x)

def fetch_hl_positions(address: str):
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
    curr = {p["symbol"]: p for p in curr_list}
    alerts = []

    for sym, p in curr.items():
        side = p["side"] or "-"
        size = float(p.get("sizeUsd") or 0.0)
        entry = float(p.get("entryPrice") or 0.0)
        liq = float(p.get("liqPrice") or 0.0)
        pnl = float(p.get("uPnl") or 0.0)
        lev = float(p.get("leverage") or 0.0)

        prev_p = prev.get(sym)
        if prev_p is None or float(prev_p.get("sizeUsd") or 0.0) <= 0:
            alerts.append(
                f"[Hyperliquid] {whale_name}\n"
                f"OPEN {side} {sym}\n"
                f"Size: {fmt_usd(size)}  Lev: x{lev:.1f}\n"
                f"Entry: {entry:.2f}  Liq: {liq:.2f}\n"
                f"Time: {now_iso()}"
            )
        else:
            prev_side = prev_p.get("side")
            prev_size = float(prev_p.get("sizeUsd") or 0.0)
            if prev_side != side and size > 0:
                alerts.append(
                    f"[Hyperliquid] {whale_name}\n"
                    f"FLIP {sym}: {prev_side} → {side}\n"
                    f"New size: {fmt_usd(size)}  Entry: {entry:.2f}\n"
                    f"Time: {now_iso()}"
                )
            else:
                if prev_size > 0:
                    change_pct = abs(size - prev_size) / prev_size * 100
                    if change_pct >= SIZE_CHANGE_PCT:
                        direction = "Increase" if size > prev_size else "Reduce"
                        alerts.append(
                            f"[Hyperliquid] {whale_name}\n"
                            f"{direction} {sym} {side}\n"
                            f"{fmt_usd(prev_size)} → {fmt_usd(size)}  ({change_pct:.1f}%)\n"
                            f"Entry: {entry:.2f}  Liq: {liq:.2f}\n"
                            f"Time: {now_iso()}"
                        )
            if size > 0:
                pnl_pct = (pnl / size) * 100 if size else 0.0
                if abs(pnl_pct) >= PNL_ALERT_PCT:
                    sign = "Profit" if pnl_pct > 0 else "Loss"
                    alerts.append(
                        f"[Hyperliquid] {sign} • {whale_name}\n"
                        f"{sym} {side} | PNL: {fmt_usd(pnl)} ({pnl_pct:.1f}%)\n"
                        f"Size: {fmt_usd(size)}  Entry: {entry:.2f}\n"
                        f"Time: {now_iso()}"
                    )

    for sym, prev_p in prev.items():
        if sym not in curr or float(curr.get(sym, {}).get("sizeUsd") or 0.0) <= 0:
            if float(prev_p.get("sizeUsd") or 0.0) > 0:
                alerts.append(
                    f"[Hyperliquid] {whale_name}\n"
                    f"CLOSE {prev_p.get('side')} {sym}\n"
                    f"Prev size: {fmt_usd(float(prev_p.get('sizeUsd') or 0.0))}\n"
                    f"Time: {now_iso()}"
                )
    return alerts, curr

def run_hyperliquid_tracker(wallets=None):
    wallets = wallets or DEFAULT_WALLETS
    state = load_state()
    if "positions" not in state or not isinstance(state["positions"], dict):
        state["positions"] = {}

    for w in wallets:
        name = w["name"]
        addr = w["address"].strip()
        prev = state["positions"].get(name, {})

        boot_key = f"_boot_sent_hl::{name}"
        if not state.get(boot_key):
            send_line_message(f"[Hyperliquid] tracker started\n{name}")
            state[boot_key] = True
            save_state(state)

        pos = fetch_hl_positions(addr)
        alerts, new_positions = compare_and_alert(name, prev, pos)
        for msg in alerts:
            send_line_message(msg)
            time.sleep(0.3)

        state["positions"][name] = new_positions
        save_state(state)
