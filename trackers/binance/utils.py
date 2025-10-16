# trackers/binance/utils.py
import time
import requests

# Candidate endpoints (try in order)
ENDPOINTS = [
    "https://www.binance.com/bapi/cms/v1/friendly/notice/search",
    "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query",
]

# Browser-like headers
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json",
    "Origin": "https://www.binance.com",
    "Referer": "https://www.binance.com/",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

SESSION_INIT_TIMEOUT = 6
REQUEST_TIMEOUT = 10
RETRIES = 2
RETRY_DELAY = 1.0


def _normalize_response_json(json_data):
    """
    Try common shapes and return list of article-like dicts.
    """
    if not json_data:
        return []

    # common structure A: { "data": { "articles": [...] } }
    d = json_data.get("data") if isinstance(json_data, dict) else None
    if isinstance(d, dict):
        if "articles" in d and isinstance(d["articles"], list):
            return d["articles"]
        # some endpoints use "items" or "records"
        if "items" in d and isinstance(d["items"], list):
            return d["items"]
        if "records" in d and isinstance(d["records"], list):
            return d["records"]

    # common structure B: { "data": [...] }
    if isinstance(json_data.get("data"), list):
        return json_data.get("data")

    # fallback: top-level list
    if isinstance(json_data, list):
        return json_data

    # fallback: check keys that look like lists
    for k, v in (json_data.items() if isinstance(json_data, dict) else []):
        if isinstance(v, list):
            return v

    return []


def fetch_binance_articles(catalog_id=48, page=1, page_size=20, lang="en"):
    """
    Robust fetch for Binance support announcements.
    Tries multiple endpoints, performs a lightweight session init (GET homepage)
    to obtain cookies, and posts JSON payload. Returns list of article dicts.
    """
    session = requests.Session()
    session.headers.update(HEADERS)

    # Try to warm up session (get cookies / any dynamic headers)
    try:
        session.get("https://www.binance.com/", timeout=SESSION_INIT_TIMEOUT)
    except Exception:
        # ignore, sometimes blocked - we still proceed to POST attempts
        pass

    payload_variants = [
        # variant for /friendly/notice/search (used by site)
        {"page": page, "pageSize": page_size, "catalogId": catalog_id, "language": lang},
        # variant for /composite/article/list/query
        {"catalogId": str(catalog_id), "pageNo": page, "pageSize": page_size},
        # generic fallback
        {"catalogId": catalog_id, "page": page, "pageSize": page_size},
    ]

    last_exc = None
    for endpoint in ENDPOINTS:
        for payload in payload_variants:
            for attempt in range(RETRIES + 1):
                try:
                    resp = session.post(endpoint, json=payload, timeout=REQUEST_TIMEOUT)
                    # If server responds 403, 429, we may back off and retry
                    if resp.status_code == 200:
                        j = resp.json()
                        articles = _normalize_response_json(j)
                        return articles
                    else:
                        last_exc = Exception(f"{resp.status_code} {resp.reason} for url: {endpoint}")
                        # small backoff on 4xx/5xx
                        time.sleep(RETRY_DELAY * (attempt + 1))
                except Exception as e:
                    last_exc = e
                    time.sleep(RETRY_DELAY * (attempt + 1))
            # try next payload
        # try next endpoint

    # if we reach here, everything failed
    print(f"Binance fetch error (catalog {catalog_id}):", last_exc)
    return []
