import time
import hashlib
import json
import requests
from typing import Optional
from loguru import logger

from config.settings import SHOPEE_AFFILIATE_APP_ID, SHOPEE_AFFILIATE_SECRET

class ShopeeAffiliateHelper:
    """
    Module tự động chuyển đổi link sản phẩm Shopee gốc thành Link Affiliate (Tiếp thị liên kết):
    - Hỗ trợ Shopee Affiliate Open API (GraphQL API v3)
    - Tự động gắn SubID (ví dụ: sub_id=kol_01_device_5554) để đo lường chính xác hoa hồng từng KOL
    - Fallback thông minh sang link tracking có tham số referral nếu chưa đăng ký Open API key
    """

    GRAPHQL_API = "https://affiliate.shopee.vn/api/v3/gql"

    def __init__(self, app_id: str = SHOPEE_AFFILIATE_APP_ID, secret: str = SHOPEE_AFFILIATE_SECRET):
        self.app_id = app_id
        self.secret = secret

    def generate_affiliate_link(self, product_url: str, kol_id: str = "kol_01", device_id: str = "emulator-5554") -> str:
        """
        Tạo link tiếp thị liên kết chuẩn:
        - Nếu có APP_ID và SECRET: gọi GraphQL API lấy short link (https://s.shopee.vn/xxx)
        - Nếu không có: tự động sinh affiliate tracking URL có SubID để theo dõi
        """
        if not product_url:
            return ""

        sub_id = f"{kol_id}_{device_id.replace('-', '_')}"

        if self.app_id and self.secret:
            try:
                timestamp = int(time.time())
                payload_json = json.dumps({
                    "query": """
                    mutation {
                        generateShortLink(input: {
                            originUrl: "%s",
                            subIds: ["%s"]
                        }) {
                            shortLink
                        }
                    }
                    """ % (product_url, sub_id)
                })

                factor = f"{self.app_id}{timestamp}{payload_json}{self.secret}"
                signature = hashlib.sha256(factor.encode("utf-8")).hexdigest()

                headers = {
                    "Authorization": f"SHA256 Credential={self.app_id}, Timestamp={timestamp}, Signature={signature}",
                    "Content-Type": "application/json"
                }

                resp = requests.post(self.GRAPHQL_API, data=payload_json, headers=headers, timeout=8)
                if resp.status_code == 200:
                    data = resp.json()
                    short_link = data.get("data", {}).get("generateShortLink", {}).get("shortLink")
                    if short_link:
                        logger.info(f"🔗 [Affiliate] Đã sinh link tiếp thị: {short_link} (SubID: {sub_id})")
                        return short_link

                logger.warning(f"⚠️ Shopee Affiliate API phản hồi không thành công, dùng link fallback.")
            except Exception as e:
                logger.warning(f"⚠️ Lỗi kết nối Shopee Affiliate API: {e}. Chuyển sang link fallback.")

        # Fallback tracking URL chuẩn gắn SubID
        sep = "&" if "?" in product_url else "?"
        fallback_url = f"{product_url}{sep}utm_source=an_video_{sub_id}&utm_medium=affiliates&utm_campaign={kol_id}"
        return fallback_url

    def extract_item_and_shop_id(self, url: str) -> tuple:
        """Trích xuất item_id và shop_id từ URL Shopee."""
        import re
        # Format 1: shopee.vn/product/{shop_id}/{item_id}
        m1 = re.search(r"product/(\d+)/(\d+)", url)
        if m1:
            return m1.group(2), m1.group(1)

        # Format 2: shopee.vn/ten-san-pham-i.{shop_id}.{item_id}
        m2 = re.search(r"-i\.(\d+)\.(\d+)", url)
        if m2:
            return m2.group(2), m2.group(1)

        return "", ""
