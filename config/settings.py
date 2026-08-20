import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Database
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "database" / "shopee_matrix.db"))

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Box Phone Settings
MIN_POST_INTERVAL_MINUTES = int(os.getenv("MIN_POST_INTERVAL_MINUTES", "15"))
MAX_POST_INTERVAL_MINUTES = int(os.getenv("MAX_POST_INTERVAL_MINUTES", "20"))
DAILY_POST_LIMIT_PER_DEVICE = int(os.getenv("DAILY_POST_LIMIT_PER_DEVICE", "50"))

# Server Config
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

# Asset Directories
OUTPUT_DIR = BASE_DIR / "output"
ASSETS_DIR = BASE_DIR / "assets"
KOL_FACES_DIR = ASSETS_DIR / "kol_faces"
BGM_DIR = ASSETS_DIR / "bgm"
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
KOL_FACES_DIR.mkdir(parents=True, exist_ok=True)
BGM_DIR.mkdir(parents=True, exist_ok=True)
BACKGROUNDS_DIR.mkdir(parents=True, exist_ok=True)
