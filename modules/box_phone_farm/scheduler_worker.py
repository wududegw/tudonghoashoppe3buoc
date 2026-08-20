import os
import time
import random
import threading
from pathlib import Path
from datetime import datetime, date
from config.settings import (
    MIN_POST_INTERVAL_MINUTES, MAX_POST_INTERVAL_MINUTES, 
    DAILY_POST_LIMIT_PER_DEVICE, OUTPUT_DIR
)
from database.db_manager import db
from modules.box_phone_farm.adb_manager import ADBManager
from modules.box_phone_farm.shopee_automator import ShopeeAutomator
from utils.notifier import send_telegram_alert

class DeviceWorkerThread(threading.Thread):
    def __init__(self, device_id: str, kol_channel: str, kol_name: str, daily_limit: int = DAILY_POST_LIMIT_PER_DEVICE):
        super().__init__(daemon=True)
        self.device_id = device_id
        self.kol_channel = kol_channel
        self.kol_name = kol_name
        self.daily_limit = daily_limit
        self.adb = ADBManager()
        self.automator = ShopeeAutomator(device_id)
        self.is_running = True

    def run(self):
        print(f"🟢 [Worker {self.kol_name}] Bắt đầu tiến trình quản lý máy {self.device_id}...")
        
        while self.is_running:
            try:
                # 1. Kiểm tra hạn mức 50 video/ngày
                daily_count = db.get_device_daily_posted_count(self.device_id)
                if daily_count >= self.daily_limit:
                    print(f"🏆 [Worker {self.kol_name}] Đã đạt mốc tối đa {daily_count}/{self.daily_limit} video hôm nay! Tạm nghỉ...")
                    time.sleep(1800) # Đợi 30 phút kiểm tra lại (qua ngày mới tự reset)
                    continue

                # 2. Lấy công việc tiếp theo từ hàng đợi
                job = db.get_next_job_for_device(self.device_id)
                if not job:
                    # Chưa có video render sẵn, đợi 30s check lại
                    time.sleep(30)
                    continue

                print(f"📥 [Worker {self.kol_name}] Nhận job: {job['title']} (ID: {job['item_id']})")
                
                # 3. Chuẩn bị đường dẫn video và screenshot
                video_file = job["video_path"]
                screen_shot_file = str(OUTPUT_DIR / f"success_{self.device_id.replace(':', '_')}_{job['item_id']}.png")
                remote_dest = "/sdcard/DCIM/Camera/temp_post.mp4"

                # 4. Thực hiện chu trình Đăng & Gắn Link
                try:
                    # Nạp video vào máy
                    pushed = self.adb.push_video(self.device_id, video_file, remote_dest)
                    if not pushed:
                        raise Exception("Không thể push video sang Box Phone qua ADB")

                    # Thực hiện đăng bài và gắn thẻ
                    self.automator.post_video_with_product_link(
                        product_url=job["product_url"],
                        caption_text=job["caption"],
                        screenshot_path=screen_shot_file
                    )

                    # Ghi nhận vào DB
                    db.record_posted(
                        item_id=job["item_id"],
                        shop_id="",
                        kol_channel=self.kol_channel,
                        device_id=self.device_id,
                        video_path=video_file,
                        caption=job["caption"]
                    )
                    db.update_queue_status(job["id"], "POSTED")

                    # Cập nhật số đếm mới
                    new_count = db.get_device_daily_posted_count(self.device_id)
                    success_msg = f"🎉 [Kênh {self.kol_name}] Đã đăng video thành công ({new_count}/{self.daily_limit})\n📦 SP: {job['title']}\n🔗 Link: {job['product_url']}"
                    send_telegram_alert(success_msg, photo_path=screen_shot_file)

                except Exception as e:
                    print(f"❌ [Worker {self.kol_name}] Lỗi khi đăng: {e}")
                    db.update_queue_status(job["id"], "FAILED", error_msg=str(e))
                    send_telegram_alert(f"⚠️ [Kênh {self.kol_name}] Lỗi đăng video SP {job['item_id']}: {e}")

                finally:
                    # ==========================================================
                    # BƯỚC QUAN TRỌNG NHẤT: XÓA SẠCH VIDEO TRÊN MÁY VÀ SERVER
                    # ==========================================================
                    self.adb.cleanup_video(self.device_id, remote_dest)
                    if os.path.exists(video_file):
                        os.remove(video_file)

                # 5. Nghỉ ngẫu nhiên 15 - 20 phút trước khi sang lượt tiếp theo
                sleep_min = random.randint(MIN_POST_INTERVAL_MINUTES, MAX_POST_INTERVAL_MINUTES)
                print(f"☕ [Worker {self.kol_name}] Nghỉ {sleep_min} phút trước lượt tiếp theo...")
                time.sleep(sleep_min * 60)

            except Exception as outer_e:
                print(f"[Worker {self.kol_name}] Lỗi ngoại lệ vòng lặp: {outer_e}")
                time.sleep(60)
