# main.py
from trackers.market.top_gainers import check_top_gainers
from trackers.market.trending_coins import check_trending_coins
from trackers.market.recently_added import check_recently_added
from trackers.dex.new_pairs import check_new_dex_pairs

from trackers.news.crypto_news import check_crypto_news_all

from trackers.hyperliquid_tracker import run_hyperliquid_tracker
from trackers.onchain_tracker import run_onchain_tracker


def main():
    # =============== MARKET / SOCIAL SENTIMENT ===============
    try:
        # 1) เหรียญขึ้นแรง 24h
        check_top_gainers(threshold_pct=20)
    except Exception as e:
        print("Top Gainers error:", e)

    try:
        # 2) เหรียญที่คนค้นหาเยอะสุด
        check_trending_coins(limit=5)
    except Exception as e:
        print("Trending Coins error:", e)

    try:
        # 3) เหรียญเพิ่งถูกเพิ่มบน CoinGecko (New Listing)
        check_recently_added(limit=5)
    except Exception as e:
        print("Recently Added error:", e)

    try:
        # 4) คู่เทรดใหม่บน DEX (Gem/Meme)
        check_new_dex_pairs(liq_threshold=50000, limit=5)
    except Exception as e:
        print("New DEX Pairs error:", e)

    try:
        # 5) ข่าวจาก CryptoPanic (important / bullish / bearish / rising)
        check_crypto_news_all(limit_each=3)
    except Exception as e:
        print("Crypto News error:", e)

    # =============== WHALE / DERIVATIVES ===============
    try:
        # ตำแหน่ง Perp ของวาฬบน Hyperliquid
        run_hyperliquid_tracker()
    except Exception as e:
        print("Hyperliquid tracker error:", e)

    try:
        # ธุรกรรม Stablecoin ของวาฬ (ข้ามถ้าไม่มี API KEY)
        run_onchain_tracker()
    except Exception as e:
        print("On-chain tracker error:", e)


if __name__ == "__main__":
    main()
