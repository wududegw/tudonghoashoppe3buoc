import requests
from pathlib import Path
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_alert(message: str, photo_path: str = None):
    """Gửi thông báo và ảnh chụp màn hình về Telegram Bot"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[Telegram Alert - Mock]: {message}")
        return

    try:
        if photo_path and Path(photo_path).exists():
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            with open(photo_path, "rb") as f:
                requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "caption": message}, files={"photo": f}, timeout=15)
        else:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=15)
    except Exception as e:
        print(f"[Notifier] Lỗi gửi tin nhắn Telegram: {e}")
