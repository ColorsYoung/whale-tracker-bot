# main.py
from trackers.market.top_gainers import check_top_gainers
from trackers.market.trending_coins import check_trending_coins
from trackers.market.recently_added import check_recently_added

from trackers.dex.new_pairs import check_new_dex_pairs
from trackers.news.crypto_news import check_crypto_news  # ✅ ใช้ฟังก์ชันใหม่

from trackers.hyperliquid_tracker import run_hyperliquid_tracker
from trackers.onchain_tracker import run_onchain_tracker


def main():
    # =============== MARKET / SOCIAL SENTIMENT ===============
    try:
        check_top_gainers(threshold_pct=20)
    except Exception as e:
        print("Top Gainers error:", e)

    try:
        check_trending_coins(limit=5)
    except Exception as e:
        print("Trending Coins error:", e)

    try:
        check_recently_added(limit=5)
    except Exception as e:
        print("Recently Added error:", e)

    try:
        check_new_dex_pairs(liq_threshold=50000, limit=5)
    except Exception as e:
        print("DEX error:", e)

    try:
        # ✅ ใช้ฟังก์ชันใหม่ check_crypto_news
        check_crypto_news(limit=5)
    except Exception as e:
        print("CryptoPanic error:", e)

    # =============== WHALE / DERIVATIVES ===============
    try:
        run_hyperliquid_tracker()
    except Exception as e:
        print("Hyperliquid tracker error:", e)

    try:
        run_onchain_tracker()
    except Exception as e:
        print("On-chain tracker error:", e)


if __name__ == "__main__":
    main()
