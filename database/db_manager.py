import sqlite3
import json
from datetime import datetime, date
from pathlib import Path
from config.settings import DB_PATH

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        schema_file = Path(__file__).parent / "schema.sql"
        with self.get_connection() as conn:
            if schema_file.exists():
                with open(schema_file, "r", encoding="utf-8") as f:
                    conn.executescript(f.read())
            conn.commit()

    def is_product_posted_on_channel(self, item_id: str, kol_channel: str) -> bool:
        """Kiểm tra sản phẩm đã từng được đăng trên kênh này chưa"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM posted_history WHERE item_id = ? AND kol_channel = ?",
                (str(item_id), kol_channel)
            )
            return cursor.fetchone() is not None

    def is_product_in_queue(self, item_id: str, kol_channel: str) -> bool:
        """Kiểm tra sản phẩm đang nằm trong hàng đợi của kênh chưa"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM video_queue WHERE item_id = ? AND kol_channel = ? AND status IN ('PENDING', 'PROCESSING', 'RENDERED')",
                (str(item_id), kol_channel)
            )
            return cursor.fetchone() is not None

    def add_product(self, item_id: str, shop_id: str, title: str, price: str, 
                    original_price: str, url: str, raw_images: list, category: str):
        """Lưu thông tin sản phẩm mới"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO products 
                (item_id, shop_id, title, price, original_price, url, raw_images, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(item_id), str(shop_id), title, price, original_price, url, json.dumps(raw_images), category))
            conn.commit()

    def add_to_queue(self, item_id: str, kol_channel: str, device_id: str, 
                     product_url: str, title: str, price: str, caption: str, video_path: str = None):
        """Thêm video vào hàng đợi đăng bài"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO video_queue 
                (item_id, kol_channel, device_id, product_url, title, price, caption, video_path, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(item_id), kol_channel, device_id, product_url, title, price, caption, video_path, 'RENDERED' if video_path else 'PENDING'))
            conn.commit()
            return cursor.lastrowid

    def get_next_job_for_device(self, device_id: str):
        """Lấy công việc render xong sẵn sàng đăng trên máy cụ thể"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM video_queue 
                WHERE device_id = ? AND status = 'RENDERED'
                ORDER BY created_at ASC LIMIT 1
            """, (device_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def update_queue_status(self, job_id: int, status: str, video_path: str = None, error_msg: str = None):
        """Cập nhật trạng thái của video trong hàng đợi"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE video_queue 
                SET status = ?, video_path = COALESCE(?, video_path), error_msg = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, video_path, error_msg, job_id))
            conn.commit()

    def record_posted(self, item_id: str, shop_id: str, kol_channel: str, 
                      device_id: str, video_path: str, caption: str):
        """Ghi nhận đã đăng thành công và tăng đếm ngày trên thiết bị"""
        today_str = date.today().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # 1. Ghi vào lịch sử chống trùng
            cursor.execute("""
                INSERT OR IGNORE INTO posted_history 
                (item_id, shop_id, kol_channel, device_id, video_path, caption)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (str(item_id), str(shop_id), kol_channel, device_id, video_path, caption))

            # 2. Cập nhật thống kê thiết bị
            cursor.execute("""
                INSERT INTO device_stats (device_id, kol_channel, today_date, posted_count, last_posted_at)
                VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(device_id) DO UPDATE SET
                    posted_count = CASE WHEN today_date = ? THEN posted_count + 1 ELSE 1 END,
                    today_date = ?,
                    last_posted_at = CURRENT_TIMESTAMP
            """, (device_id, kol_channel, today_str, today_str, today_str))
            conn.commit()

    def get_device_daily_posted_count(self, device_id: str) -> int:
        """Lấy số lượng video đã đăng trong ngày của thiết bị"""
        today_str = date.today().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT posted_count FROM device_stats 
                WHERE device_id = ? AND today_date = ?
            """, (device_id, today_str))
            row = cursor.fetchone()
            if row:
                return row['posted_count']
            return 0

    def get_all_device_stats(self):
        """Lấy thống kê tất cả các máy trong Box Phone"""
        today_str = date.today().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT device_id, kol_channel, today_date, posted_count, last_posted_at
                FROM device_stats
            """)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

db = DatabaseManager()
