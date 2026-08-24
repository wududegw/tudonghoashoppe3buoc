import time
import random
import requests
from typing import List, Dict, Any, Optional

from config.settings import CRAWLER_CONFIG
from database.db_manager import DatabaseManager
from modules.crawler.product_parser import ProductParser

# Danh sách User-Agents chuẩn để fallback nếu chưa cài fake_useragent
FALLBACK_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
]

class ShopeeCrawler:
    """Crawler thuần Python lấy dữ liệu sản phẩm trực tiếp từ Shopee."""

    SEARCH_API_URL = "https://shopee.vn/api/v4/search/search_items"
    ITEM_DETAIL_API_URL = "https://shopee.vn/api/v4/item/get"

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()
        self.session = requests.Session()
        try:
            from fake_useragent import UserAgent
            self.ua = UserAgent()
        except Exception:
            self.ua = None

    def _get_headers(self) -> Dict[str, str]:
        """Tạo headers giả lập trình duyệt để tránh bị Shopee chặn."""
        if self.ua:
            try:
                user_agent = self.ua.random
            except Exception:
                user_agent = random.choice(FALLBACK_USER_AGENTS)
        else:
            user_agent = random.choice(FALLBACK_USER_AGENTS)

        return {
            "User-Agent": user_agent,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://shopee.vn/",
            "X-Requested-With": "XMLHttpRequest",
            "X-Shopee-Language": "vi",
            "X-API-SOURCE": "rweb",
            "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="122", "Chromium";v="122"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }

    def search_products(
        self,
        keyword: str,
        limit: int = 20,
        sort_by: str = "sales",
        min_sold: int = None,
        min_rating: float = None,
        auto_save_db: bool = True
    ) -> List[Dict[str, Any]]:
        """Quét sản phẩm theo từ khóa tìm kiếm."""
        if min_sold is None:
            min_sold = CRAWLER_CONFIG.get("min_sold", 0)
        if min_rating is None:
            min_rating = CRAWLER_CONFIG.get("min_rating", 0.0)

        print(f"[*] [Crawler] Dang quet tu khoa: '{keyword}' (limit={limit}, sortBy={sort_by})...")

        params = {
            "by": sort_by if sort_by != "sales" else "sales",
            "keyword": keyword,
            "limit": limit * 2,
            "newest": 0,
            "order": "desc",
            "page_type": "search",
            "scenario": "PAGE_GLOBAL_SEARCH",
            "version": 2
        }

        try:
            headers = self._get_headers()
            response = self.session.get(
                self.SEARCH_API_URL,
                headers=headers,
                params=params,
                timeout=CRAWLER_CONFIG.get("request_timeout", 15)
            )

            if response.status_code != 200:
                print(f"[!] Shopee API tra ve ma loi HTTP {response.status_code}")
                return []

            data = response.json()
            items_raw = data.get("items", [])
            if not items_raw:
                print(f"[-] Khong tim thay san pham nao cho '{keyword}'")
                return []

            valid_products = []
            saved_count = 0
            duplicate_count = 0

            for raw in items_raw:
                parsed = ProductParser.parse_search_item(raw)
                if not parsed:
                    continue

                # Kiểm tra lọc chất lượng
                if not ProductParser.filter_product(
                    parsed,
                    min_sold=min_sold,
                    min_rating=min_rating,
                    min_images=1
                ):
                    continue

                # Kiểm tra chống trùng database
                if self.db.is_product_exists(parsed["item_id"], parsed["shop_id"]):
                    duplicate_count += 1
                    continue

                # Tự động lưu vào SQLite nếu bật auto_save_db
                if auto_save_db:
                    product_id = self.db.insert_product(parsed)
                    if product_id:
                        parsed["id"] = product_id
                        saved_count += 1

                valid_products.append(parsed)

                if len(valid_products) >= limit:
                    break

            print(f"[+] [Crawler] Quet xong '{keyword}': {len(valid_products)} SP hop le, Luu moi: {saved_count}, Trung: {duplicate_count}")
            return valid_products

        except Exception as e:
            print(f"[x] [Crawler] Loi khi quet '{keyword}': {str(e)}")
            return []

    def crawl_keywords_list(self, keywords: Optional[List[str]] = None, limit_per_keyword: int = 10) -> List[Dict[str, Any]]:
        """Quét hàng loạt theo danh sách từ khóa."""
        if keywords is None:
            keywords = CRAWLER_CONFIG.get("default_keywords", [])

        all_collected = []
        for kw in keywords:
            products = self.search_products(keyword=kw, limit=limit_per_keyword, auto_save_db=True)
            all_collected.extend(products)
            delay = CRAWLER_CONFIG.get("delay_between_requests", 1.5) + random.uniform(0.3, 0.8)
            time.sleep(delay)

        return all_collected
