# whale-tracker-bot
whale-tracker-bot

---

## ✅ สิ่งที่ต้องเตรียม

### 1) สร้าง LINE Bot (Messaging API)
- ไปที่ https://developers.line.biz/
- Create Provider (เช่น WhaleTracker)
- Create Channel → Messaging API
- ออก **Channel access token (long-lived)**

### 2) หา userId หรือ groupId
- ใช้ webhook หรือ Messaging API test tool
- ตัวอย่าง userID: `U3d25c3cf4db5e573e0d91d19348e029a`

---

## ✅ ตั้งค่า GitHub Secrets

ไปที่  
`GitHub Repo → Settings → Secrets and variables → Actions → New repository secret`

เพิ่มค่าต่อไปนี้:

| Secret Name | Value |
|-------------|----------------------------------------------|
| LINE_CHANNEL_ACCESS_TOKEN | (Token จาก LINE Bot) |
| LINE_TARGET_ID | userId หรือ groupId |
| WALLET | 0xb317d2bc2d3d2df5fa441b5bae0ab9d8b07283ae |
| ETHERSCAN_API_KEY | (สมัครฟรีจาก etherscan.io) |

*(สามารถตั้งเพิ่มเติม เช่น THRESHOLD_USD ในไฟล์ track.yml)*

---

## ✅ ทดสอบรันครั้งแรก

1. ไปที่แท็บ **Actions**
2. เลือก Workflow: **Whale Tracker (LINE Bot)**
3. กดปุ่ม **Run workflow**
4. ดูที่ LINE → จะได้รับข้อความเริ่มต้น เช่น:  
   ✅ Whale Tracker Started...

---

## ✅ การทำงานจริง

- Workflow จะรัน **ทุก 5 นาทีอัตโนมัติ**
- `track_whale.py` จะตรวจธุรกรรม ERC20 จากกระเป๋าวาฬ
- ถ้าโอน stablecoin ≥ 100,000 → ส่งแจ้งเตือน LINE
- สามารถอัปเกรดเพิ่มการตรวจ Long/Short จาก Hyperliquid API

---

## ✅ อัปเกรดในอนาคต (แนะนำ)
- ดึง Position (Long/Short/Size/Liq/PnL) จาก Hyperliquid
- เก็บ state เพื่อตรวจเฉพาะการเปลี่ยนแปลง
- ส่ง Flex Message หรือ Rich Message ผ่าน LINE Bot
- รองรับหลายกระเป๋า / หลายเชน
- บันทึก log หรือแจ้ง Telegram / Discord เพิ่ม

---

## ✅ หมายเหตุ
- อย่า commit Token ลง GitHub → ใช้ Secrets เท่านั้น!
---

