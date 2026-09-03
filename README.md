# 🚀 Shopee Video Automation - Hệ Thống Tự Động Hóa Shopee Affiliate Review

Hệ thống tự động hóa khép kín chuyên biệt cho **Shopee Affiliate Video**: Quét sản phẩm bán chạy -> Tự động tạo link tiếp thị liên kết (SubID từng KOL) -> Gemini AI sinh kịch bản review -> Edge-TTS lồng tiếng Việt -> MoviePy dựng Video Review 9:16 chuyên nghiệp -> Nạp hàng đợi cho Box Phone Farm.

---

## ⚡ LUỒNG HOẠT ĐỘNG HOÀN CHỈNH

```
[ BƯỚC 1: QUÉT SẢN PHẨM & TẠO LINK AFFILIATE ]
  • Quét Shopee theo từ khóa / top bán chạy, lọc hàng còn tồn kho (stock > 0).
  • Lọc chất lượng: Lượt bán, đánh giá >= 4.5 sao, ảnh HD gốc 1080p.
  • Tự động phân loại ngành hàng và gán về 1 trong 10 Profile KOL độc quyền.
  • TỰ ĐỘNG TẠO LINK SHOPEE AFFILIATE (Gắn SubID đo lường hoa hồng cho từng KOL).
  • Chống trùng lặp tuyệt đối trong cơ sở dữ liệu SQLite.
           │
           ▼
[ BƯỚC 2: SẢN XUẤT VIDEO REVIEW CHUYÊN NGHIỆP (LOCAL 100% FREE) ]
  • Gemini AI sinh kịch bản 12-15s theo chuẩn AIDA (Hook 3s -> Công năng 8s -> CTA Giỏ hàng 4s).
  • Bộ lọc từ cấm chính sách kiểm duyệt của Shopee/TikTok (không đọc giá cứng).
  • Edge-TTS lồng tiếng Việt chuẩn ngữ điệu (Nam/Nữ theo từng phong cách KOL).
  • MoviePy Engine: Hiệu ứng chuyển động Ken-Burns (Zoom mượt mà), font tiếng Việt Unicode sắc nét.
  • Tự động hòa âm nhạc nền BGM (12%) + Header KOL + Nút kêu gọi giỏ hàng góc trái.
  • Xuất ra Video MP4 hoàn chỉnh 9:16 (1080x1920) không tốn chi phí API.
           │
           ▼
[ BƯỚC 3: BOX PHONE FARM AUTO-POST (CHỜ KÍCH HOẠT) ]
  • Đẩy video vào máy qua ADB + quét thư viện Media Scanner.
  • UIAutomator2 tự động mở Shopee Video, gắn link sản phẩm, điền caption, bấm Đăng.
  • Xóa video dọn dẹp bộ nhớ -> Nghỉ giãn cách 15-20 phút giữa các lần đăng.
```

---

## ⚙️ CẤU HÌNH & KHỞI CHẠY

### 1. Cài đặt thư viện:
```bash
pip install -r requirements.txt
```

### 2. Cấu hình file `.env`:
Tạo file `.env` từ `.env.example` và điền thông tin:
```ini
# Gemini API Key (Sinh kịch bản review viral)
GEMINI_API_KEY=your_gemini_api_key

# Chế độ dựng video: "local" (MoviePy + Edge-TTS miễn phí 100%) hoặc "api" (D-ID)
VIDEO_ENGINE_MODE=local

# Shopee Affiliate Open API (Tùy chọn: Để tạo shortlink chính thống)
SHOPEE_AFFILIATE_APP_ID=
SHOPEE_AFFILIATE_SECRET=

# Telegram Bot (Báo cáo kết quả)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 3. Kiểm thử từng bước:

- **Kiểm thử Bước 1 (Crawler & Tạo Link Affiliate)**:
  ```bash
  python test_step1_crawler.py
  ```

- **Kiểm thử Bước 2 (Kịch bản AI + Giọng đọc + Dựng Video MP4 9:16)**:
  ```bash
  python test_step2_kol_video.py
  ```

- **Mở Dashboard Web Quản Lý Cào Dữ Liệu (Port 8888)**:
  ```bash
  python run_step1_ui.py
  ```
  *(Truy cập `http://localhost:8888` để xem danh sách, lọc, copy Excel/JSON, xuất CSV và bấm nút Tạo Video trực tiếp trên từng sản phẩm)*.

- **Chạy toàn bộ quy trình Bước 1 và Bước 2**:
  ```bash
  python main.py
  ```
