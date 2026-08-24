from typing import Dict, Any, List, Optional
from datetime import datetime

class ProductParser:
    IMAGE_CDN_BASE = "https://down-vn.img.susercontent.com/file/"

    @classmethod
    def get_hd_image_url(cls, image_id: str) -> str:
        """Tạo link ảnh HD gốc từ hash image ID của Shopee."""
        if not image_id:
            return "https://via.placeholder.com/150"
        if image_id.startswith("http"):
            return image_id
        return f"{cls.IMAGE_CDN_BASE}{image_id}"

    @classmethod
    def parse_search_item(cls, item_raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Phân tích dữ liệu 1 sản phẩm từ Search API / V4 API của Shopee."""
        try:
            item_basic = item_raw.get("item_basic", item_raw)

            item_id = str(item_basic.get("itemid", item_basic.get("item_id", "")))
            shop_id = str(item_basic.get("shopid", item_basic.get("shop_id", "")))
            name = item_basic.get("name", "").strip()

            if not item_id or not shop_id or not name:
                return None

            # Tên Shop
            shop_name = item_basic.get("shop_name", "")
            if not shop_name:
                shop_location = item_basic.get("shop_location", "")
                shop_name = f"Shop Official #{shop_id}" if not shop_location else f"Shop {shop_location}"

            # Xử lý giá tiền (Shopee API thường lưu giá x100000)
            raw_price = item_basic.get("price", 0)
            raw_price_before = item_basic.get("price_before_discount", raw_price)

            price = raw_price / 100000 if raw_price > 1000000 else raw_price
            price_before = raw_price_before / 100000 if raw_price_before > 1000000 else raw_price_before

            if price_before < price:
                price_before = price

            discount_percent = 0
            if price_before > 0 and price < price_before:
                discount_percent = int(round((1 - price / price_before) * 100))

            # Lượt bán & Đánh giá sao
            historical_sold = item_basic.get("historical_sold", item_basic.get("sold", 0))
            rating_star = 5.0
            rating_info = item_basic.get("item_rating", {})
            if isinstance(rating_info, dict):
                rating_star = round(rating_info.get("rating_star", 5.0), 1)
            elif isinstance(rating_info, (int, float)):
                rating_star = round(float(rating_info), 1)

            # Danh sách ảnh HD
            raw_images = item_basic.get("images", [])
            images = []
            for img in raw_images:
                if img:
                    images.append(cls.get_hd_image_url(img))

            # Cover image nếu chưa có trong list
            cover_image = item_basic.get("image")
            if cover_image:
                cover_url = cls.get_hd_image_url(cover_image)
                if cover_url not in images:
                    images.insert(0, cover_url)

            if not images:
                images = ["https://via.placeholder.com/300"]

            # Ngày tạo / Ngày đăng
            ctime = item_basic.get("ctime", 0)
            if ctime and ctime > 0:
                created_date = datetime.fromtimestamp(ctime).strftime("%d/%m/%Y %H:%M:%S")
            else:
                created_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            # Link sản phẩm chuẩn
            product_url = f"https://shopee.vn/product/{shop_id}/{item_id}"
            category = item_basic.get("cat_name", item_basic.get("category_name", "Chung"))

            return {
                "item_id": item_id,
                "shop_id": shop_id,
                "shop_name": shop_name,
                "title": name,
                "price": float(price),
                "price_formatted": f"{int(price):,}".replace(",", "."),
                "price_before_discount": float(price_before),
                "discount_percent": discount_percent,
                "historical_sold": int(historical_sold),
                "rating_star": float(rating_star),
                "product_url": product_url,
                "affiliate_url": "",
                "thumb_image": images[0],
                "images": images,
                "category": category,
                "created_date": created_date
            }
        except Exception as e:
            return None

    @classmethod
    def filter_product(cls, product: Dict[str, Any], min_sold: int = 0, min_rating: float = 0.0, min_images: int = 1) -> bool:
        """Kiểm tra sản phẩm có đạt chuẩn theo cấu hình lọc của người dùng."""
        if not product:
            return False
        if product.get("historical_sold", 0) < min_sold:
            return False
        if product.get("rating_star", 0) < min_rating:
            return False
        if len(product.get("images", [])) < min_images:
            return False
        return True
