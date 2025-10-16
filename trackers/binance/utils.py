import requests

BINANCE_API = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Origin": "https://www.binance.com",
    "Referer": "https://www.binance.com/",
    "X-UI-REQUEST-TRACE": "true"
}

def fetch_binance_articles(catalog_id=48, page=1, page_size=20):
    payload = {
        "catalogId": str(catalog_id),
        "pageNo": page,
        "pageSize": page_size
    }
    try:
        r = requests.post(BINANCE_API, json=payload, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return (r.json().get("data") or {}).get("articles", []) or []
    except Exception as e:
        print(f"Binance fetch error (catalog {catalog_id}):", e)
        return []
