from datetime import datetime
from core.state_manager import load_state, save_state
from core.line_notifier import send_line_message
from .utils import fetch_binance_articles

def _fmt_dt(ms):
    try:
        return datetime.fromtimestamp(ms/1000).strftime("%Y-%m-%d %H:%M")
    except:
        return "-"

def _is_margin(title: str) -> bool:
    title = title or ""
    keys = [
        "Isolated Margin",
        "Cross Margin",
        "Margin Trading",
        "Margin Pair",
        "Added to Margin",
        "Borrowable",
        "Collateral"
    ]
    return any(k in title for k in keys)

def check_binance_margin_pairs():
    state = load_state()
    seen = set(state.get("binance_margin_ids", []))
    articles = fetch_binance_articles(catalog_id=48)

    for a in articles:
        aid = str(a.get("id", ""))
        title = a.get("title", "") or ""

        if not _is_margin(title):
            continue
        if aid in seen:
            continue

        when = _fmt_dt(a.get("releaseDate", 0))
        link = f"https://www.binance.com/en/support/announcement/{aid}"
        msg = f"[Binance Margin]\n{title}\nTime: {when}\n{link}"
        print(msg)
        send_line_message(msg)

        seen.add(aid)

    state["binance_margin_ids"] = list(seen)
    save_state(state)
