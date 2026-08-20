# 🛒 SHOPEE VIDEO MATRIX & BOX PHONE FARM AUTOMATION 🚀

Hệ thống tự động hóa khép kín:
1. **Quét sản phẩm:** Nhận dữ liệu từ Google Apps Script / Crawler.
2. **Chống trùng sản phẩm:** Tra cứu database, không bao giờ làm lại sản phẩm đã đăng.
3. **Nhà máy AI Video 10 KOL:** Tự xóa phông/chữ cũ (`rembg`) + Gemini viết kịch bản giật tít + Edge-TTS lồng tiếng riêng cho từng KOL + Render video 9:16 có chuyển động Ken-Burns.
4. **Box Phone Farm Auto-Post:** Đẩy 1 video duy nhất vào máy -> Gắn chính xác Link sản phẩm -> Điền Caption/Hashtags chuẩn font tiếng Việt -> Bấm Đăng -> Xóa sạch video giải phóng bộ nhớ -> Nghỉ 15-20 phút -> Lặp lại (Tối đa 50 video/ngày/máy).

---

## 📁 Cấu trúc Dự án

```
shopee_video_automation/
├── config/
│   ├── kols_config.json          # Cấu hình 10 KOL, 10 Kênh, 10 Box Phone, giọng đọc
│   └── settings.py               # Cấu hình đường dẫn, API keys, hạn mức
├── database/
│   ├── db_manager.py             # Quản lý SQLite, chống trùng, log đăng bài
│   └── schema.sql                # DDL bảng products, posted_history, video_queue, device_stats
├── modules/
│   ├── crawler_receiver/
│   │   ├── api_server.py         # FastAPI Webhook nhận dữ liệu từ Google Apps Script
│   │   └── dispatcher.py         # AI Classifier điều hướng SP về đúng KOL
│   ├── video_engine/
│   │   ├── image_cleaner.py      # Xóa chữ/logo shop cũ (rembg), ghép studio 3D
│   │   ├── script_generator.py   # Gemini AI sinh kịch bản giật tít + caption + hashtags
│   │   ├── tts_generator.py      # Edge-TTS sinh giọng đọc riêng biệt
│   │   └── video_composer.py     # Ghép video 9:16 + Text Banner + Anti-duplicate
│   ├── box_phone_farm/
│   │   ├── adb_manager.py        # Quản lý kết nối ADB, nạp file, dọn dẹp bộ nhớ máy
│   │   ├── shopee_automator.py   # uiautomator2 thao tác mở Shopee, gắn link, điền caption
│   │   └── scheduler_worker.py   # Vòng lặp đăng bài 15-20p, kiểm soát 50 video/ngày
├── utils/
│   └── notifier.py               # Báo cáo kết quả, gửi screenshot về Telegram Bot
├── main.py                       # Điểm khởi chạy toàn bộ hệ thống
└── requirements.txt              # Danh sách thư viện Python
```

---

## ⚡ Hướng dẫn Cài đặt & Vận hành

### 1. Cài đặt môi trường Python
```bash
cd C:\Users\Administrator\.gemini\antigravity\scratch\shopee_video_automation
pip install -r requirements.txt
```

### 2. Cấu hình File `.env`
Tạo file `.env` từ `.env.example`:
```env
GEMINI_API_KEY=your_gemini_api_key
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 3. Cài đặt trên từng máy Box Phone
1. Bật **Tùy chọn nhà phát triển (Developer Options)** -> Bật **Gỡ lỗi USB (USB Debugging)**.
2. Cài file `ADBKeyBoard.apk` vào tất cả các máy trong Box Phone để hỗ trợ gõ Tiếng Việt có dấu và icon:
   ```bash
   adb -s <DEVICE_ID> install ADBKeyBoard.apk
   adb -s <DEVICE_ID> ime set com.android.adbkeyboard/.AdbIME
   ```

### 4. Khởi chạy Hệ thống
```bash
python main.py
```

---

## 🌐 Tích hợp với Google Apps Script (Crawler của bạn)

Trong mã nguồn Google Apps Script của bạn, sau khi quét được sản phẩm mới, thêm đoạn code sau để bắn sang Webhook của hệ thống:

```javascript
function sendProductToAutomationServer(productData) {
  var serverUrl = "http://YOUR_SERVER_IP:8000/api/webhook/shopee-product";
  
  var payload = {
    "item_id": String(productData.item_id),
    "shop_id": String(productData.shop_id),
    "title": productData.name,
    "price": productData.price_format,
    "original_price": productData.original_price_format,
    "url": productData.link,
    "images": productData.images, // Mảng các URL ảnh HD
    "category": productData.category_name || ""
  };

  var options = {
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify(payload),
    "muteHttpExceptions": true
  };

  var response = UrlFetchApp.fetch(serverUrl, options);
  Logger.log(response.getContentText());
}
```
