# 🚀 Shopee Video Automation - Hệ Thống Tự Động Hóa Khép Kín 3 Bước

Quy trình tự động hóa khép kín tối giản: Quét sản phẩm trên máy -> Gọi API sinh Video Review với KOL -> Box Phone Farm tự động đăng Shopee Video.

---

## ⚡ LUỒNG HOẠT ĐỘNG 3 BƯỚC CỰC KỲ TINH GỌN

```
[ BƯỚC 1: QUÉT SẢN PHẨM THUẦN PYTHON ]
  • Quét trực tiếp Shopee trên máy theo từ khóa / top bán chạy.
  • Lấy trọn bộ: ID, Tên, Giá, Đánh giá, và Ảnh sản phẩm HD.
  • Tự động chống trùng lặp trong SQLite Database.
           │
           ▼
[ BƯỚC 2: GỌI API LÀM VIDEO REVIEW VỚI KOL ]
  • Lấy ảnh sản phẩm vừa quét + KOL ngành tương ứng.
  • Tạo kịch bản review ngắn gọn (12-15s) + câu kết: "Bấm vào giỏ hàng góc trái để xem".
  • GỌI THẲNG API LÀM VIDEO (D-ID / HeyGen...) -> Nhận về Video MP4 hoàn chỉnh.
           │
           ▼
[ BƯỚC 3: BOX PHONE FARM AUTO-POST ]
  • Đẩy 1 video duy nhất vào máy qua ADB.
  • Tự động mở Shopee Video, gắn link sản phẩm, điền caption, bấm Đăng.
  • Xóa video giải phóng bộ nhớ -> Nghỉ 15-20 phút -> Lặp lại.
```

---

## ⚙️ CẤU HÌNH & KHỞI CHẠY

1. **Cài đặt thư viện**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Cấu hình file `.env`**:
   ```ini
   GEMINI_API_KEY=your_gemini_api_key
   AI_VIDEO_PROVIDER=d-id
   AI_VIDEO_API_KEY=your_video_api_key
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```

3. **Chạy thử nghiệm Bước 1 (Python Crawler)**:
   ```bash
   python test_step1_crawler.py
   ```

4. **Khởi chạy toàn bộ hệ thống**:
   ```bash
   python main.py
   ```
