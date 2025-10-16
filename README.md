# Crypto Whale Tracker Bot

A modular, production-ready crypto monitoring system that tracks:
- Binance listings and newly added trading pairs
- Margin and Futures pair additions
- Hyperliquid whale perpetual positions (open/close/flip/size change/PNL)
- On-chain stablecoin whale transfers (USDT, USDC, DAI)

Send instant alerts via LINE whenever high-impact events occur.

---

ระบบติดตามคริปโตอัตโนมัติ (Modular / Production-Grade) ที่สามารถ:
- ตรวจจับเหรียญใหม่จะลิสต์บน Binance
- ตรวจจับคู่เทรด Spot / Margin / Futures ที่ถูกเพิ่ม
- ติดตามโพสิชัน Perpetual ของวาฬบน Hyperliquid (เปิด/ปิด/กลับฝั่ง/เพิ่ม size/PNL)
- ติดตามธุรกรรม Stablecoin ก้อนใหญ่บนบล็อกเชน (USDT/USDC/DAI)

**และแจ้งเตือนผ่าน LINE แบบ Real-time**


## ✅ Key Features / ฟีเจอร์หลัก

### 1️⃣ Binance Listing Alerts (เหรียญใหม่จะลิสต์)
- ตรวจสอบประกาศจาก Binance CMS (catalogId=48)
- จับเฉพาะหัวข้อที่มีคำว่า “Will List”, “Lists”, “Launchpool”, etc.
- แจ้งเตือนทันทีเมื่อ Binance จะลิสต์เหรียญใหม่
- ใช้ state.json เพื่อกันแจ้งซ้ำ

---

### 2️⃣ New Trading Pairs Detection (Spot / Margin / Futures)
**แยกชัดเจนเป็น 3 โมดูล:**
- Spot Pairs: เช่น “Adds XYZ/USDT”
- Margin Pairs: Isolated / Cross / Borrowable / Collateral
- Futures / Perpetual Contracts: USDT-M, USDⓈ-M, Coin-M

แต่ละหมวดมี state แยกกัน → ไม่แจ้งซ้ำ

---

### 3️⃣ Hyperliquid Whale Position Tracker
ติดตามโพสิชัน Perpetual ของ “วาฬ” แบบเรียลไทม์:
- เปิดโพสิชันใหม่
- ปิดโพสิชัน
- เพิ่ม/ลดขนาดโพสิชันตาม % ที่กำหนด (SIZE_CHANGE_PCT)
- กลับฝั่ง (LONG → SHORT)
- PnL ถึงเกณฑ์ (PNL_ALERT_PCT)

ออกแบบแบบ modular → เพิ่มวาฬหลายตัวได้

---

### 4️⃣ On-chain Stablecoin Whale Transfers
- ใช้ Etherscan API ดึงธุรกรรม ERC20
- ตรวจจับการโอน USDT / USDC / DAI มูลค่าเกิน THRESHOLD_USD
- แจ้งเตือนพร้อมลิงก์ธุรกรรม
- state.json ใช้สำหรับจำว่ารันครั้งแรก

---

### 5️⃣ LINE Notifications (Real-time)
- แจ้งเตือนผ่าน LINE Official API
- รองรับทั้ง userId (U…) หรือ groupId (C…)
- หั่นข้อความยาวอัตโนมัติ (max 4900 chars)
- ใช้ฟังก์ชันกลาง send_line_message()

---

### 6️⃣ Modular Architecture (ออกแบบให้ขยายง่าย)
- core/ → config, state, notifier
- trackers/ → Binance, Hyperliquid, On-chain
- main.py → orchestration (เรียงลำดับการทำงาน)
- แก้ไข / เพิ่มโมดูลใหม่ได้โดยไม่กระทบส่วนอื่น

---

### 7️⃣ GitHub Actions Automation
- รันอัตโนมัติทุก 5 นาที (schedule)
- ดึงโค้ด, ติดตั้ง dependencies, รัน tracker ทั้งหมด
- commit state.json กลับ repo เพื่อจำสถานะ
- รองรับ manual run (workflow_dispatch)


## 🧠 Project Architecture / โครงสร้างโปรเจกต์

โปรเจกต์นี้ออกแบบแบบ **Modular / Clean / Scalable**  
เพื่อให้สามารถขยาย, ดูแล, แก้ไขได้ง่ายในระยะยาว

whale-tracker-bot/
│
├── core/ # โมดูลกลาง ใช้ร่วมกันทุก tracker
│ ├── config.py # อ่าน environment variables, ตัวแปรสำคัญ
│ ├── state_manager.py # load_state() / save_state() → อ่าน/เขียน state.json
│ └── line_notifier.py # send_line_message() → ส่ง LINE แจ้งเตือน
│
├── trackers/ # ติดตามเหตุการณ์จากหลายแหล่ง (modular)
│ ├── hyperliquid_tracker.py # ติดตามโพสิชันวาฬบน Hyperliquid
│ ├── onchain_tracker.py # ตรวจจับธุรกรรม stablecoin ก้อนใหญ่จาก Etherscan
│ │
│ └── binance/ # แยก Binance ออกเป็น 4 โมดูลชัดเจน
│ ├── init.py
│ ├── listing.py # เหรียญใหม่จะลิสต์ (Will List)
│ ├── spot_pairs.py # เพิ่ม Spot trading pairs
│ ├── margin_pairs.py # เพิ่ม Margin / Isolated / Cross
│ └── futures_pairs.py # เพิ่ม Futures / Perpetual contracts
│
├── main.py # จุดควบคุมหลัก: เรียก tracker ทุกตัว
│
├── state.json # เก็บสถานะล่าสุดเพื่อกันแจ้งซ้ำ (auto create)
├── requirements.txt # Python dependencies
└── README.md # (ไฟล์นี้)



