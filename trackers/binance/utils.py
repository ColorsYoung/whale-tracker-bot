import requests

BINANCE_API = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
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
