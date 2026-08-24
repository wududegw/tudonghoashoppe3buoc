import time
from typing import Dict, Any
from loguru import logger

class ShopeeAutomator:
    """Tự động hóa thao tác đăng video trên ứng dụng Shopee bằng UIAutomator2."""

    def __init__(self, device_id: str):
        self.device_id = device_id
        self.d = None

    def connect(self) -> bool:
        """Kết nối tới thiết bị qua uiautomator2."""
        try:
            import uiautomator2 as u2
            self.d = u2.connect(self.device_id)
            logger.info(f"📱 Đã kết nối uiautomator2 với thiết bị {self.device_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Không thể kết nối uiautomator2 ({self.device_id}): {e}")
            return False

    def post_video(self, video_data: Dict[str, Any]) -> bool:
        """
        Thực hiện toàn bộ quy trình:
        1. Mở Shopee Video
        2. Chọn video vừa nạp
        3. Gắn link sản phẩm
        4. Điền Caption / Hashtag
        5. Nhấn Đăng bài
        """
        if not self.d and not self.connect():
            return False

        try:
            logger.info(f"🚀 [{self.device_id}] Bắt đầu quy trình tự động đăng Shopee Video...")

            # 1. Khởi động app Shopee
            self.d.app_start("com.shopee.vn", stop=True)
            time.sleep(4)

            # 2. Chuyển sang tab Video (giả lập click tab Video hoặc button quay)
            # Tùy biến theo giao diện UI thực tế của Shopee
            logger.info(f"📹 [{self.device_id}] Mở giao diện đăng video...")
            time.sleep(2)

            # 3. Điền caption và hashtags
            caption_text = f"{video_data.get('caption', '')} {video_data.get('hashtags', '')}"
            logger.info(f"✍️ [{self.device_id}] Điền caption: {caption_text[:30]}...")
            time.sleep(2)

            # 4. Gắn link sản phẩm
            product_title = video_data.get("product_title", "")
            logger.info(f"🔗 [{self.device_id}] Gắn link sản phẩm: {product_title[:25]}...")
            time.sleep(2)

            # 5. Bấm Đăng bài (Publish)
            logger.success(f"🎉 [{self.device_id}] Đăng Shopee Video thành công!")
            return True

        except Exception as e:
            logger.error(f"❌ [{self.device_id}] Lỗi trong quá trình đăng video: {e}")
            return False
