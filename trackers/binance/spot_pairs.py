import re
from datetime import datetime
from core.state_manager import load_state, save_state
from core.line_notifier import send_line_message
from .utils import fetch_binance_articles

def _fmt_dt(ms):
    try:
        return datetime.fromtimestamp(ms/1000).strftime("%Y-%m-%d %H:%M")
    except:
        return "-"

def _is_spot_pair(title: str) -> bool:
    title = title or ""
    if "Will List" in title:
        return False
    keys = ["Adds Trading Pairs", "Will Add", "Adds"]
    has_pair = bool(re.search(r"[A-Z0-9]{2,}/[A-Z]{2,6}", title))
    return any(k in title for k in keys) and has_pair

def check_binance_spot_pairs():
    state = load_state()
    seen = set(state.get("binance_spot_ids", []))
    articles = fetch_binance_articles(catalog_id=48)

    for a in articles:
        aid = str(a.get("id", ""))
        title = a.get("title", "") or ""

        if not _is_spot_pair(title):
            continue
        if aid in seen:
            continue

        when = _fmt_dt(a.get("releaseDate", 0))
        link = f"https://www.binance.com/en/support/announcement/{aid}"

        msg = f"[Binance Spot Pair]\n{title}\nTime: {when}\n{link}"
        print(msg)
        send_line_message(msg)

        seen.add(aid)

    state["binance_spot_ids"] = list(seen)
    save_state(state)
