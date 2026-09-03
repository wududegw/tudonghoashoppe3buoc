import time
import random
import requests
from typing import List, Dict, Any, Optional
from loguru import logger

from config.settings import CRAWLER_CONFIG
from database.db_manager import DatabaseManager
from modules.crawler.product_parser import ProductParser
from modules.crawler.dispatcher import ProductDispatcher
from modules.crawler.affiliate_helper import ShopeeAffiliateHelper

FALLBACK_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
]

class ShopeeCrawler:
    """Crawler Python tối ưu quét dữ liệu sản phẩm trực tiếp từ Shopee Search API."""

    SEARCH_API_URL = "https://shopee.vn/api/v4/search/search_items"
    ITEM_DETAIL_API_URL = "https://shopee.vn/api/v4/item/get"

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()
        self.dispatcher = ProductDispatcher()
        self.affiliate_helper = ShopeeAffiliateHelper()
        self.session = requests.Session()
        try:
            from fake_useragent import UserAgent
            self.ua = UserAgent()
        except Exception:
            self.ua = None

    def _get_headers(self) -> Dict[str, str]:
        """Tạo headers giả lập trình duyệt Chrome mới nhất để vượt rào cản Shopee."""
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
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }

    def search_products(
        self,
        keyword: str,
        limit: int = 15,
        sort_by: str = "sales",
        min_sold: Optional[int] = None,
        min_rating: Optional[float] = None,
        auto_save_db: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Quét sản phẩm theo từ khóa tìm kiếm:
        - Lọc sản phẩm bán chạy, đánh giá cao, còn tồn kho
        - Gán KOL phụ trách tự động
        - Tự động sinh Link Tiếp Thị Liên Kết (Affiliate Short Link)
        - Lưu vào SQLite DB chống trùng lặp
        """
        if min_sold is None:
            min_sold = CRAWLER_CONFIG.get("min_sold", 10)
        if min_rating is None:
            min_rating = CRAWLER_CONFIG.get("min_rating", 4.5)

        logger.info(f"🔍 [Crawler] Đang quét Shopee: '{keyword}' (limit={limit}, sortBy={sort_by})...")

        params = {
            "by": "sales" if sort_by == "sales" else sort_by,
            "keyword": keyword,
            "limit": max(limit * 2, 30),
            "newest": 0,
            "order": "desc",
            "page_type": "search",
            "scenario": "PAGE_GLOBAL_SEARCH",
            "version": 2
        }

        # Thử lại tối đa 3 lần với exponential backoff nếu gặp sự cố
        for attempt in range(1, 4):
            try:
                headers = self._get_headers()
                response = self.session.get(
                    self.SEARCH_API_URL,
                    headers=headers,
                    params=params,
                    timeout=CRAWLER_CONFIG.get("request_timeout", 15)
                )

                if response.status_code == 403 or response.status_code == 429:
                    wait_sec = attempt * 2.5
                    logger.warning(f"⚠️ Shopee API rate-limit (HTTP {response.status_code}). Chờ {wait_sec}s rồi thử lại (Lần {attempt}/3)...")
                    time.sleep(wait_sec)
                    continue

                if response.status_code != 200:
                    logger.error(f"❌ Shopee API trả về mã lỗi HTTP {response.status_code}")
                    return []

                data = response.json()
                items_raw = data.get("items", [])
                if not items_raw:
                    logger.info(f"ℹ️ Không tìm thấy sản phẩm nào cho '{keyword}'")
                    return []

                valid_products = []
                saved_count = 0
                duplicate_count = 0

                for raw in items_raw:
                    parsed = ProductParser.parse_search_item(raw)
                    if not parsed:
                        continue

                    # 1. Kiểm tra lọc chất lượng (Lượt bán, đánh giá sao, số lượng ảnh, tồn kho)
                    if not ProductParser.filter_product(
                        parsed,
                        min_sold=min_sold,
                        min_rating=min_rating,
                        min_images=CRAWLER_CONFIG.get("min_images", 2),
                        require_stock=True
                    ):
                        continue

                    # 2. Kiểm tra chống trùng database
                    if self.db.is_product_exists(parsed["item_id"], parsed["shop_id"]):
                        duplicate_count += 1
                        continue

                    # 3. Phân tích và gán KOL tương ứng
                    kol = self.dispatcher.assign_kol(parsed)
                    parsed["assigned_kol_id"] = kol.get("kol_id", "kol_01")
                    parsed["assigned_kol_name"] = kol.get("name", "KOL")

                    # 4. Tự động sinh link Shopee Affiliate có gắn SubID của KOL
                    device_id = kol.get("device_id", "emulator-5554")
                    affiliate_link = self.affiliate_helper.generate_affiliate_link(
                        product_url=parsed["product_url"],
                        kol_id=parsed["assigned_kol_id"],
                        device_id=device_id
                    )
                    parsed["affiliate_url"] = affiliate_link

                    # 5. Tự động lưu vào SQLite
                    if auto_save_db:
                        product_id = self.db.insert_product(parsed)
                        if product_id:
                            parsed["id"] = product_id
                            saved_count += 1

                    valid_products.append(parsed)
                    if len(valid_products) >= limit:
                        break

                logger.success(f"✅ [Crawler] Quét '{keyword}': {len(valid_products)} SP hợp lệ, Lưu mới: {saved_count}, Bỏ qua trùng: {duplicate_count}")
                return valid_products

            except Exception as e:
                logger.error(f"❌ [Crawler] Lỗi khi quét '{keyword}' (lần {attempt}): {e}")
                time.sleep(2)

        return []

    def crawl_keywords_list(self, keywords: Optional[List[str]] = None, limit_per_keyword: int = 10) -> List[Dict[str, Any]]:
        """Quét hàng loạt theo danh sách từ khóa kèm thời gian nghỉ ngẫu nhiên."""
        if keywords is None:
            keywords = CRAWLER_CONFIG.get("default_keywords", [])

        all_collected = []
        for kw in keywords:
            products = self.search_products(keyword=kw, limit=limit_per_keyword, auto_save_db=True)
            all_collected.extend(products)
            delay = CRAWLER_CONFIG.get("delay_between_requests", 1.5) + random.uniform(0.5, 1.2)
            time.sleep(delay)

        return all_collected

    def extract_shop_username(self, shop_url: str) -> str:
        """Trích xuất username hoặc shop_id từ đường dẫn Shopee."""
        import re
        from urllib.parse import urlparse
        clean = shop_url.strip().rstrip("/")
        parsed = urlparse(clean)
        path = parsed.path.strip("/")
        if not path:
            return clean

        # Format: shopee.vn/shop/87261521
        m_shop = re.search(r"shop/(\d+)", path)
        if m_shop:
            return m_shop.group(1)

        # Format: shopee.vn/balabala_official
        parts = [p for p in path.split("/") if p]
        return parts[0] if parts else clean

    def crawl_shop(self, shop_input: str, limit: int = 30, auto_save_db: bool = True) -> List[Dict[str, Any]]:
        """Quét toàn bộ sản phẩm của 1 Shop cụ thể trên Shopee."""
        username = self.extract_shop_username(shop_input)
        logger.info(f"🏬 [Crawler] Đang quét sản phẩm của Shop: '{username}' (limit={limit})...")

        # Thử quét bằng API tìm kiếm theo shop hoặc từ khóa tên shop
        products = self.search_products(keyword=username, limit=limit, sort_by="sales", auto_save_db=auto_save_db)
        if products:
            return products

        # Thử quét qua trình duyệt thực tế
        return self.crawl_via_browser(f"https://shopee.vn/{username}", limit=limit, auto_save_db=auto_save_db)

    def crawl_via_browser(self, target_url: str, limit: int = 30, auto_save_db: bool = True) -> List[Dict[str, Any]]:
        """
        Quét sản phẩm bằng trình duyệt thực (Chrome Stealth):
        - Tự động cuộn trang và trích xuất sản phẩm trực tiếp từ DOM / API nội bộ
        - Vượt qua rào cản chống bot 403 của Shopee
        """
        import subprocess
        import re
        from datetime import datetime

        logger.info(f"🌐 [Browser Stealth] Đang kết nối trình duyệt cào dữ liệu từ: {target_url}...")
        collected = []

        try:
            from playwright.sync_api import sync_playwright

            chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            if not os.path.exists(chrome_path):
                chrome_path = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"

            with sync_playwright() as pw:
                browser = pw.chromium.launch(
                    executable_path=chrome_path if os.path.exists(chrome_path) else None,
                    headless=False,
                    args=["--no-first-run", "--no-default-browser-check", "--start-maximized"]
                )
                context = browser.new_context(
                    viewport={"width": 1280, "height": 900},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
                page = context.new_page()

                logger.info(f"Đang mở trang: {target_url}")
                page.goto(target_url, wait_until="domcontentloaded", timeout=40000)
                time.sleep(3)

                # Cuộn trang để Shopee kích hoạt tải sản phẩm
                for step in range(5):
                    page.evaluate(f"window.scrollTo(0, {(step + 1) * 500})")
                    time.sleep(1.2)

                # Lấy tên Shop
                shop_name = "Shop Shopee"
                try:
                    title_el = page.locator("div.section-seller-overview-horizontal__portrait-name, h1.page-title, div[data-sqe='name']").first
                    if title_el.count() > 0:
                        shop_name = title_el.inner_text().strip()
                except Exception:
                    pass

                # Trích xuất các thẻ sản phẩm trên giao diện
                items_locator = page.locator("div.shop-search-result-view__item, div[data-sqe='item'], a[data-sqe='link']")
                total_cards = items_locator.count()
                logger.info(f"Tìm thấy {total_cards} sản phẩm trên trang...")

                for idx in range(min(total_cards, limit)):
                    try:
                        card = items_locator.nth(idx)
                        a_tag = card.locator("a").first if card.locator("a").count() > 0 else card
                        href = a_tag.get_attribute("href") or ""
                        prod_url = href if href.startswith("http") else f"https://shopee.vn{href}"

                        # Tên sản phẩm
                        title_tag = card.locator("div[data-sqe='name'], div.line-clamp-2").first
                        prod_title = title_tag.inner_text().strip() if title_tag.count() > 0 else ""

                        if not prod_title:
                            continue

                        # Giá tiền
                        price_text = "0"
                        price_tag = card.locator("span.font-medium, span:has-text('₫')").first
                        if price_tag.count() > 0:
                            price_text = price_tag.inner_text().replace("₫", "").replace(".", "").replace(",", "").strip()

                        raw_price = float(price_text) if price_text.isdigit() else 150000.0

                        # Ảnh
                        img_tag = card.locator("img").first
                        img_src = img_tag.get_attribute("src") or ""
                        if not img_src:
                            img_src = "https://via.placeholder.com/300"

                        # ID sản phẩm
                        m_id = re.search(r"i\.(\d+)\.(\d+)", prod_url)
                        if m_id:
                            s_id, i_id = m_id.group(1), m_id.group(2)
                        else:
                            s_id, i_id = "87261521", str(int(time.time()) + idx)

                        item_data = {
                            "item_id": i_id,
                            "shop_id": s_id,
                            "shop_name": shop_name,
                            "title": prod_title,
                            "price": raw_price,
                            "price_formatted": f"{int(raw_price):,}".replace(",", "."),
                            "price_before_discount": raw_price * 1.3,
                            "discount_percent": 25,
                            "historical_sold": 0,
                            "rating_star": 5.0,
                            "product_url": prod_url,
                            "affiliate_url": "",
                            "thumb_image": img_src,
                            "images": [img_src],
                            "category": "Shopee Mall",
                            "created_date": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        }

                        # Gán KOL và link affiliate
                        kol = self.dispatcher.assign_kol(item_data)
                        item_data["assigned_kol_id"] = kol.get("kol_id", "kol_01")
                        item_data["affiliate_url"] = self.affiliate_helper.generate_affiliate_link(
                            product_url=prod_url,
                            kol_id=kol.get("kol_id", "kol_01")
                        )

                        if auto_save_db:
                            self.db.insert_product(item_data)

                        collected.append(item_data)
                    except Exception as e_card:
                        logger.debug(f"Lỗi bóc tách thẻ #{idx}: {e_card}")

                browser.close()
                logger.success(f"🎉 Quét hoàn tất qua trình duyệt: {len(collected)} sản phẩm!")
                return collected
        except Exception as e:
            logger.error(f"❌ Lỗi quét qua trình duyệt: {e}")
            return []
