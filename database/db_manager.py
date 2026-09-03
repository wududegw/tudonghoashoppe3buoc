import sqlite3
import json
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from config.settings import DATABASE_PATH

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

SAMPLE_INIT_ITEMS = [
    {
        "item_id": "229871101",
        "shop_id": "87261521",
        "shop_name": "Balabala Official Store",
        "title": "Balabala IP Búp Bê Mặt Dây Chuyền Thời Trang Trẻ Em",
        "price": 158371,
        "price_before_discount": 220000,
        "discount_percent": 28,
        "historical_sold": 0,
        "rating_star": 5.0,
        "product_url": "https://shopee.vn/product/87261521/229871101",
        "thumb_image": "https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lsi5o1k47l73ba",
        "images": ["https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lsi5o1k47l73ba"],
        "category": "Thời trang Trẻ Em",
        "created_date": "30/07/2026 18:53:06"
    },
    {
        "item_id": "229871102",
        "shop_id": "87261521",
        "shop_name": "Balabala Official Store",
        "title": "Áo thun dài tay trẻ em Balabala Lót Nỉ Mùa Thu Đông",
        "price": 300240,
        "price_before_discount": 420000,
        "discount_percent": 29,
        "historical_sold": 0,
        "rating_star": 5.0,
        "product_url": "https://shopee.vn/product/87261521/229871102",
        "thumb_image": "https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lsi5o1k49zsjec",
        "images": ["https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lsi5o1k49zsjec"],
        "category": "Thời trang Trẻ Em",
        "created_date": "30/07/2026 18:25:20"
    },
    {
        "item_id": "229871103",
        "shop_id": "87261521",
        "shop_name": "Balabala Official Store",
        "title": "Bộ Quần Áo Bé Gái Balabala Mùa Thu Phong Cách Hàn Quốc",
        "price": 357480,
        "price_before_discount": 500000,
        "discount_percent": 29,
        "historical_sold": 0,
        "rating_star": 5.0,
        "product_url": "https://shopee.vn/product/87261521/229871103",
        "thumb_image": "https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lsi5o1k4beg000",
        "images": ["https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lsi5o1k4beg000"],
        "category": "Thời trang Trẻ Em",
        "created_date": "30/07/2026 18:25:17"
    },
    {
        "item_id": "229871104",
        "shop_id": "87261521",
        "shop_name": "Balabala Official Store",
        "title": "Balabala Bé Đầm Trẻ Sơ Sinh Trẻ Em Mùa Hè Dễ Thương",
        "price": 473040,
        "price_before_discount": 600000,
        "discount_percent": 21,
        "historical_sold": 0,
        "rating_star": 5.0,
        "product_url": "https://shopee.vn/product/87261521/229871104",
        "thumb_image": "https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lsi5o1k4cuzp00",
        "images": ["https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lsi5o1k4cuzp00"],
        "category": "Thời trang Trẻ Em",
        "created_date": "30/07/2026 18:25:14"
    },
    {
        "item_id": "229871105",
        "shop_id": "87261521",
        "shop_name": "Balabala Official Store",
        "title": "Balabala Trẻ Em Tập Đi Áo Thun Cổ Tròn Thoáng Mát",
        "price": 268920,
        "price_before_discount": 350000,
        "discount_percent": 23,
        "historical_sold": 0,
        "rating_star": 5.0,
        "product_url": "https://shopee.vn/product/87261521/229871105",
        "thumb_image": "https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lsi5o1k4e9k500",
        "images": ["https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lsi5o1k4e9k500"],
        "category": "Thời trang Trẻ Em",
        "created_date": "30/07/2026 18:25:13"
    },
    {
        "item_id": "229871106",
        "shop_id": "87261521",
        "shop_name": "Balabala Official Store",
        "title": "Áo thun bé gái balabala Quần áo Trẻ Em Họa Tiết Nơ",
        "price": 336960,
        "price_before_discount": 450000,
        "discount_percent": 25,
        "historical_sold": 0,
        "rating_star": 5.0,
        "product_url": "https://shopee.vn/product/87261521/229871106",
        "thumb_image": "https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lsi5o1k4foc000",
        "images": ["https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lsi5o1k4foc000"],
        "category": "Thời trang Trẻ Em",
        "created_date": "30/07/2026 18:25:11"
    },
    {
        "item_id": "229871107",
        "shop_id": "87261521",
        "shop_name": "Balabala Official Store",
        "title": "Balabala Bé Gái Áo Thun Cotton Mềm Mại Thấm Hút Mồ Hôi",
        "price": 336960,
        "price_before_discount": 450000,
        "discount_percent": 25,
        "historical_sold": 0,
        "rating_star": 5.0,
        "product_url": "https://shopee.vn/product/87261521/229871107",
        "thumb_image": "https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lsi5o1k4h2vw00",
        "images": ["https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lsi5o1k4h2vw00"],
        "category": "Thời trang Trẻ Em",
        "created_date": "30/07/2026 18:25:09"
    },
    {
        "item_id": "229871108",
        "shop_id": "87261521",
        "shop_name": "Balabala Official Store",
        "title": "Áo thun trẻ em balabala Áo thun Ngắn Tay In Hình",
        "price": 268920,
        "price_before_discount": 350000,
        "discount_percent": 23,
        "historical_sold": 0,
        "rating_star": 5.0,
        "product_url": "https://shopee.vn/product/87261521/229871108",
        "thumb_image": "https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lsi5o1k4ihqa00",
        "images": ["https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lsi5o1k4ihqa00"],
        "category": "Thời trang Trẻ Em",
        "created_date": "30/07/2026 18:25:07"
    },
    {
        "item_id": "339871201",
        "shop_id": "92154812",
        "shop_name": "Vanikids VN",
        "title": "Set Bộ Bé Gái Áo Yếm Lụa Phối Quần Ống Rộng Đi Chơi",
        "price": 159200,
        "price_before_discount": 220000,
        "discount_percent": 28,
        "historical_sold": 0,
        "rating_star": 5.0,
        "product_url": "https://shopee.vn/product/92154812/339871201",
        "thumb_image": "https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lsi5o1k4jwbe00",
        "images": ["https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lsi5o1k4jwbe00"],
        "category": "Thời trang Trẻ Em",
        "created_date": "30/07/2026 15:42:05"
    },
    {
        "item_id": "449871301",
        "shop_id": "66481923",
        "shop_name": "Tiny Winy - Thời trang cho bé",
        "title": "M51 Tinywiny - Váy Công Chúa Bé Gái Dự Tiệc Cao Cấp",
        "price": 400000,
        "price_before_discount": 550000,
        "discount_percent": 27,
        "historical_sold": 0,
        "rating_star": 5.0,
        "product_url": "https://shopee.vn/product/66481923/449871301",
        "thumb_image": "https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lsi5o1k4l76q00",
        "images": ["https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lsi5o1k4l76q00"],
        "category": "Thời trang Trẻ Em",
        "created_date": "30/07/2026 15:16:06"
    }
]

class DatabaseManager:
    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Khởi tạo database và nạp dữ liệu mẫu ban đầu nếu trống."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                cursor.executescript(f.read())
            conn.commit()

        # Nếu chưa có sản phẩm nào, nạp sẵn dữ liệu mẫu
        if self.get_products_count() == 0:
            for item in SAMPLE_INIT_ITEMS:
                self.insert_product(item)

    def is_product_exists(self, item_id: str, shop_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM products WHERE item_id = ? AND shop_id = ?",
                (str(item_id), str(shop_id))
            )
            return cursor.fetchone() is not None

    def insert_product(self, product_data: Dict[str, Any]) -> Optional[int]:
        item_id = str(product_data.get("item_id"))
        shop_id = str(product_data.get("shop_id"))

        if self.is_product_exists(item_id, shop_id):
            return None

        images_json = json.dumps(product_data.get("images", []), ensure_ascii=False)
        thumb_image = product_data.get("thumb_image", "")
        if not thumb_image and product_data.get("images"):
            thumb_image = product_data["images"][0]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products (
                    item_id, shop_id, shop_name, title, price, price_before_discount,
                    discount_percent, historical_sold, rating_star, product_url,
                    affiliate_url, thumb_image, images_json, category, assigned_kol_id,
                    created_date, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id,
                shop_id,
                product_data.get("shop_name", f"Shop #{shop_id}"),
                product_data.get("title", ""),
                product_data.get("price", 0.0),
                product_data.get("price_before_discount", 0.0),
                product_data.get("discount_percent", 0),
                product_data.get("historical_sold", 0),
                product_data.get("rating_star", 0.0),
                product_data.get("product_url", ""),
                product_data.get("affiliate_url", ""),
                thumb_image,
                images_json,
                product_data.get("category", ""),
                product_data.get("assigned_kol_id", ""),
                product_data.get("created_date", datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
                "pending"
            ))
            conn.commit()
            return cursor.lastrowid

    def get_all_products(self, limit: int = 1000) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            results = []
            for row in rows:
                item = dict(row)
                item["images"] = json.loads(item.get("images_json", "[]"))
                price_val = item.get("price", 0)
                item["price_formatted"] = f"{int(price_val):,}".replace(",", ".")
                results.append(item)
            return results

    def get_products_count(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM products")
            row = cursor.fetchone()
            return row["total"] if row else 0

    def clear_all_products(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products")
            cursor.execute("DELETE FROM video_queue")
            conn.commit()

    def get_pending_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE status = 'pending' ORDER BY id ASC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            results = []
            for row in rows:
                item = dict(row)
                item["images"] = json.loads(item.get("images_json", "[]"))
                results.append(item)
            return results

    def update_product_status(self, product_id: int, status: str, kol_id: Optional[str] = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if kol_id:
                cursor.execute("UPDATE products SET status = ?, assigned_kol_id = ? WHERE id = ?", (status, kol_id, product_id))
            else:
                cursor.execute("UPDATE products SET status = ? WHERE id = ?", (status, product_id))
            conn.commit()

    def add_to_video_queue(self, product_id: int, kol_id: str, script_hook: str, script_body: str, caption: str, hashtags: str) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO video_queue (product_id, kol_id, script_hook, script_body, caption, hashtags, status)
                VALUES (?, ?, ?, ?, ?, ?, 'queued')
            """, (product_id, kol_id, script_hook, script_body, caption, hashtags))
            conn.commit()
            return cursor.lastrowid

    def update_video_queue(self, queue_id: int, video_path: str, status: str = "ready_to_post", error_message: str = ""):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE video_queue SET video_path = ?, status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (video_path, status, error_message, queue_id))
            conn.commit()

    def get_ready_to_post_videos(self, limit: int = 5) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT vq.*, p.title as product_title, p.product_url, p.affiliate_url, p.item_id, p.shop_id
                FROM video_queue vq
                JOIN products p ON vq.product_id = p.id
                WHERE vq.status = 'ready_to_post'
                ORDER BY vq.id ASC LIMIT ?
            """, (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def can_device_post_today(self, device_id: str, max_limit: int = 50) -> bool:
        today_str = date.today().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT post_count FROM device_daily_stats WHERE device_id = ? AND stat_date = ?", (device_id, today_str))
            row = cursor.fetchone()
            if not row:
                return True
            return row["post_count"] < max_limit

    def increment_device_post(self, device_id: str, product_id: int, kol_id: str, video_path: str, caption: str):
        today_str = date.today().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO posted_history (product_id, kol_id, device_id, video_path, caption, status)
                VALUES (?, ?, ?, ?, ?, 'success')
            """, (product_id, kol_id, device_id, video_path, caption))

            cursor.execute("""
                INSERT INTO device_daily_stats (device_id, stat_date, post_count, last_posted_at)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(device_id, stat_date) DO UPDATE SET
                    post_count = post_count + 1,
                    last_posted_at = CURRENT_TIMESTAMP
            """, (device_id, today_str))

            cursor.execute("UPDATE products SET status = 'posted' WHERE id = ?", (product_id,))
            conn.commit()

    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            if not row:
                return None
            item = dict(row)
            item["images"] = json.loads(item.get("images_json", "[]"))
            return item

    def update_affiliate_url(self, product_id: int, affiliate_url: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET affiliate_url = ? WHERE id = ?", (affiliate_url, product_id))
            conn.commit()

    def is_product_in_queue(self, product_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM video_queue WHERE product_id = ? AND status != 'error'", (product_id,))
            return cursor.fetchone() is not None

    def get_all_device_stats(self) -> List[Dict[str, Any]]:
        today_str = date.today().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM device_daily_stats WHERE stat_date = ? ORDER BY post_count DESC", (today_str,))
            return [dict(r) for r in cursor.fetchall()]

# Singleton Database instance for convenient access across modules
db = DatabaseManager()
