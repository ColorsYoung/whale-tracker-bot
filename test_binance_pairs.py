# test_binance_pairs.py
# ✅ โค้ดนี้ไม่ดึงจาก Binance จริง
# ✅ เราจำลอง articles ขึ้นมาเอง เพื่อทดสอบ logic

from binance_pairs import _is_spot_pairs, _is_margin, _is_futures

# สร้าง test cases จำลอง
test_articles = [
    # 1) Spot Pair ใหม่
    {"id": "spot1", "title": "Binance Adds ABC/USDT and ABC/FDUSD", "releaseDate": 1730000000000},

    # 2) Margin Pair ใหม่
    {"id": "margin1", "title": "Binance Adds ABC to Isolated Margin and Cross Margin", "releaseDate": 1730000000000},

    # 3) Futures Contract ใหม่
    {"id": "futures1", "title": "Binance Futures Will Launch ABCUSDT Perpetual Contract", "releaseDate": 1730000000000},

    # 4) Listing เหรียญใหม่ (ควรถูก _is_spot_pairs ข้าม)
    {"id": "list1", "title": "Binance Will List TEST (TEST/USDT)", "releaseDate": 1730000000000},

    # 5) ข่าวอื่น (ไม่ควรจับ)
    {"id": "other1", "title": "Binance Launches Trading Competition for XYZ", "releaseDate": 1730000000000},
]

def main():
    for a in test_articles:
        title = a["title"]
        print(f"\nTITLE: {title}")

        print("is_spot_pairs:  ", _is_spot_pairs(title))
        print("is_margin:      ", _is_margin(title))
        print("is_futures:     ", _is_futures(title))


if __name__ == "__main__":
    main()
