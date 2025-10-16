from trackers.binance.listing import check_binance_listing
from trackers.binance.spot_pairs import check_binance_spot_pairs
from trackers.binance.margin_pairs import check_binance_margin_pairs
from trackers.binance.futures_pairs import check_binance_futures_pairs
from trackers.hyperliquid_tracker import run_hyperliquid_tracker
from trackers.onchain_tracker import run_onchain_tracker

def main():
    # Binance (ข่าวสำคัญที่มีผลต่อราคา)
    try:
        check_binance_listing()
        check_binance_spot_pairs()
        check_binance_margin_pairs()
        check_binance_futures_pairs()
    except Exception as e:
        print("Binance checks error:", e)

    # Hyperliquid positions ของวาฬ
    try:
        run_hyperliquid_tracker()
    except Exception as e:
        print("Hyperliquid tracker error:", e)

    # On-chain stablecoin whale transfers
    try:
        run_onchain_tracker()
    except Exception as e:
        print("On-chain tracker error:", e)

if __name__ == "__main__":
    main()
