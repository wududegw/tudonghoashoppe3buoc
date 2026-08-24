import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Paths
DATABASE_PATH = BASE_DIR / "database" / "shopee_automation.db"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "output" / "temp"
VIDEOS_DIR = BASE_DIR / "output" / "rendered_videos"
CLEANED_IMAGES_DIR = BASE_DIR / "output" / "cleaned_images"
KOLS_CONFIG_PATH = BASE_DIR / "config" / "kols_config.json"

# Make sure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
CLEANED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Crawler Settings (Bước 1)
CRAWLER_CONFIG = {
    "default_keywords": [
        "đồ gia dụng thông minh",
        "tai nghe bluetooth",
        "ốp lưng iphone",
        "bàn chải điện",
        "máy cạo râu",
        "đèn bàn học",
        "sạc dự phòng",
        "kệ để đồ đa năng",
        "nồi chiên không dầu",
        "bình giữ nhiệt"
    ],
    "min_sold": 20,           # Lọc tối thiểu 20 lượt bán
    "min_rating": 4.5,        # Đánh giá tối thiểu 4.5 sao
    "min_images": 2,          # Tối thiểu 2 ảnh HD
    "limit_per_keyword": 10,  # Số sản phẩm lấy cho mỗi từ khóa
    "request_timeout": 15,
    "delay_between_requests": 2.0  # Giây để tránh spam API
}

# Video Render Settings
VIDEO_CONFIG = {
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "duration_per_image": 3.5,  # Giây cho mỗi ảnh
    "zoom_factor": 1.15         # Ken-Burns Zoom
}

# Farm Posting Limits
FARM_CONFIG = {
    "max_posts_per_day_per_device": 50,
    "post_interval_min_minutes": 15,
    "post_interval_max_minutes": 20,
    "adb_host": os.getenv("ADB_SERVER_HOST", "127.0.0.1"),
    "adb_port": int(os.getenv("ADB_SERVER_PORT", "5037"))
}
