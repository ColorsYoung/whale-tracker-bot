import re
import requests
from datetime import datetime
from core.config import BINANCE_CMS_API
from core.line_notifier import send_line_message
from core.state_manager import load_state, save_state

def _fmt_dt(ms: int) -> str:
    try:
        return datetime.fromtimestamp(ms/1000).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "-"

def _fetch_articles():
    params = {"type": 1, "catalogId": 48, "pageNo": 1, "pageSize": 20}
    try:
        r = requests.get(BINANCE_CMS_API, params=params, timeout=12)
        r.raise_for_status()
        return (r.json().get("data") or {}).get("articles", []) or []
    except Exception as e:
        print("Fetch Binance spot pairs error:", e)
        return []

def _is_spot_pairs(title: str) -> bool:
    title = title or ""
    if "Will List" in title:
        return False
    keys = ["Adds Trading Pairs", "Will Add Trading Pairs", "Adds the following trading pairs", "Adds", "Will Add"]
    has_pair = bool(re.search(r"[A-Z0-9]{2,}/[A-Z]{2,6}", title))
    return any(k in title for k in keys) and has_pair

def check_binance_spot_pairs(articles=None):
    state = load_state()
    seen = set(str(x) for x in state.get("binance_pairs_spot", []))

    items = articles if articles is not None else _fetch_articles()
    if not items:
        return

    for a in items:
        title = a.get("title", "") or ""
        if not _is_spot_pairs(title):
            continue
        aid = str(a.get("id", ""))
        if aid in seen:
            continue
        when = _fmt_dt(int(a.get("releaseDate", 0) or 0))
        link = "https://www.binance.com/en/support/announcement/" + aid
        msg = "[Binance Spot Pair]\n" f"{title}\n" f"Time: {when}\n" f"{link}"
        print(msg)
        try:
            send_line_message(msg)
        except Exception as e:
            print("send_line_message error (spot):", e)
        seen.add(aid)

    state["binance_pairs_spot"] = list(seen)
    save_state(state)
