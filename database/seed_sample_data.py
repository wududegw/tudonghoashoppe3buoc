"""
Script nạp dữ liệu mẫu ban đầu để kiểm tra giao diện Bước 1 ngay lập tức.
"""

import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from database.db_manager import DatabaseManager

db = DatabaseManager()

sample_items = [
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

for item in sample_items:
    db.insert_product(item)

print(f"✅ Đã nạp thành công {len(sample_items)} sản phẩm mẫu vào Database.")
