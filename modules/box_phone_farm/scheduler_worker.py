import time
import random
from typing import Dict, Any
from loguru import logger

from config.settings import FARM_CONFIG
from database.db_manager import DatabaseManager
from modules.box_phone_farm.adb_manager import ADBManager
from modules.box_phone_farm.shopee_automator import ShopeeAutomator
from utils.notifier import TelegramNotifier

class SchedulerWorker:
    """Điều phối vòng lặp đăng bài tự động trên Box Phone Farm."""

    def __init__(self, db_manager: DatabaseManager = None, notifier: TelegramNotifier = None):
        self.db = db_manager or DatabaseManager()
        self.adb = ADBManager()
        self.notifier = notifier or TelegramNotifier()

    def process_one_video(self, video_item: Dict[str, Any], device_id: str) -> bool:
        """Xử lý quy trình đăng 1 video hoàn chỉnh cho 1 thiết bị."""
        product_id = video_item["product_id"]
        kol_id = video_item["kol_id"]
        video_path = video_item["video_path"]
        caption = video_item["caption"]

        # Kiểm tra hạn mức ngày
        if not self.db.can_device_post_today(device_id, FARM_CONFIG["max_posts_per_day_per_device"]):
            logger.warning(f"⚠️ Thiết bị {device_id} đã đạt giới hạn đăng {FARM_CONFIG['max_posts_per_day_per_device']} video/ngày!")
            return False

        logger.info(f"🔄 Bắt đầu đăng video cho SP #{product_id} trên {device_id}")

        # 1. Đẩy video vào máy
        remote_path = self.adb.push_video(device_id, video_path)
        if not remote_path:
            return False

        # 2. Thao tác đăng
        automator = ShopeeAutomator(device_id)
        success = automator.post_video(video_item)

        # 3. Dọn dẹp video trên máy để tránh đầy bộ nhớ
        self.adb.cleanup_video(device_id, remote_path)

        if success:
            # Ghi nhận kết quả
            self.db.increment_device_post(device_id, product_id, kol_id, video_path, caption)
            self.db.update_video_queue(video_item["id"], video_path, status="posted")

            # Gửi thông báo Telegram
            self.notifier.send_message(
                f"✅ <b>ĐÃ ĐĂNG SHOPEE VIDEO</b>\n"
                f"• SP: {video_item.get('product_title')}\n"
                f"• KOL: {kol_id} | Máy: {device_id}\n"
                f"• Caption: {caption}"
            )
            return True
        else:
            self.db.update_video_queue(video_item["id"], video_path, status="error", error_message="Lỗi auto-post")
            return False

    def run_worker_loop(self):
        """Chạy vòng lặp kiểm tra hàng đợi và đăng cách quãng 15-20 phút."""
        logger.info("⚡ Khởi động Box Phone Farm Scheduler Worker...")

        while True:
            ready_videos = self.db.get_ready_to_post_videos(limit=5)
            if not ready_videos:
                logger.info("⏳ Hàng đợi đăng bài đang trống. Chờ quét và render video mới...")
                time.sleep(30)
                continue

            for video in ready_videos:
                device_id = FARM_CONFIG.get("adb_device_id", "emulator-5554")
                self.process_one_video(video, device_id)

                # Nghỉ ngẫu nhiên 15 - 20 phút giữa các lần đăng
                wait_minutes = random.uniform(
                    FARM_CONFIG["post_interval_min_minutes"],
                    FARM_CONFIG["post_interval_max_minutes"]
                )
                logger.info(f"😴 Nghỉ {wait_minutes:.1f} phút trước khi đăng video tiếp theo...")
                time.sleep(wait_minutes * 60)
