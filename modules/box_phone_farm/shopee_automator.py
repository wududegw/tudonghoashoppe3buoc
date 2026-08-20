import time
import uiautomator2 as u2
from pathlib import Path
from modules.box_phone_farm.adb_manager import ADBManager

class ShopeeAutomator:
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.adb = ADBManager()
        self.d = None

    def connect(self):
        """Kết nối uiautomator2 với thiết bị"""
        if not self.d:
            self.d = u2.connect(self.device_id)
        return self.d

    def post_video_with_product_link(self, product_url: str, caption_text: str, screenshot_path: str = None) -> bool:
        """
        Quy trình chuẩn 6 bước:
        1. Mở Shopee -> Vào Shopee Video
        2. Chọn video vừa nạp
        3. Gắn Link sản phẩm chính xác 100%
        4. Xác thực thẻ sản phẩm đã hiển thị
        5. Điền Caption & Hashtags
        6. Bấm Đăng và xác nhận
        """
        d = self.connect()
        print(f"[ShopeeAutomator] 🚀 Bắt đầu quy trình đăng bài trên máy {self.device_id}...")

        # 1. Khởi chạy App Shopee
        d.app_start("com.shopee.vn")
        time.sleep(3)

        # 2. Click vào Tab Video (hoặc icon Camera đăng bài)
        btn_video_tab = d(text="Video")
        if btn_video_tab.exists(timeout=5):
            btn_video_tab.click()
            time.sleep(1.5)

        # Click icon Tạo Video / Máy quay
        btn_create = d(descriptionContains="Tạo") or d(resourceIdMatches=".*iv_post.*")
        if btn_create.exists(timeout=5):
            btn_create.click()
            time.sleep(2)

        # 3. Chọn video đầu tiên trong Thư viện (Chính là video duy nhất vừa nạp vào)
        btn_gallery = d(textContains="Tất cả") or d(textContains="Thư viện") or d(textContains="Gần đây")
        if btn_gallery.exists(timeout=5):
            # Click vào ô thumbnail video đầu tiên ở góc trên bên trái
            d.click(0.25, 0.25)
            time.sleep(1.5)

        btn_next = d(text="Tiếp") or d(text="Tiếp tục")
        if btn_next.exists(timeout=5):
            btn_next.click()
            time.sleep(2)

        # 4. GẮN LINK SẢN PHẨM CHÍNH XÁC 100%
        btn_add_product = d(textContains="Thêm sản phẩm") or d(textContains="Gắn thẻ")
        if not btn_add_product.exists(timeout=8):
            raise Exception("Không tìm thấy nút 'Thêm sản phẩm' trên màn hình Shopee Video")
        
        btn_add_product.click()
        time.sleep(2)

        # Tìm ô Search và dán chính xác Link sản phẩm
        search_box = d(className="android.widget.EditText")
        if not search_box.exists(timeout=5):
            d(descriptionContains="Tìm kiếm").click()
            time.sleep(1)
            search_box = d(className="android.widget.EditText")

        search_box.set_text(product_url)
        d.press("enter")
        time.sleep(2.5) # Đợi tải kết quả chính xác duy nhất

        # Bấm nút Thêm/Chọn
        btn_confirm_add = d(text="Thêm") or d(text="Chọn") or d(text="Gắn")
        if not btn_confirm_add.exists(timeout=5):
            raise Exception(f"Không tìm thấy sản phẩm trên sàn với link: {product_url}")
        
        btn_confirm_add.click()
        time.sleep(1.5)

        # 5. CHỐT CHẶN XÁC THỰC: Kiểm tra thẻ sản phẩm đã hiển thị trên màn hình chưa
        has_product_tag = d(textContains="Đã gắn").exists(timeout=5) or d(textContains="Xóa sản phẩm").exists(timeout=5)
        if not has_product_tag:
            raise Exception("CẢNH BÁO: Thẻ sản phẩm chưa được gắn thành công! Hủy đăng để bảo đảm an toàn.")

        # 6. Điền Caption & Hashtags
        caption_box = d(textContains="Thêm mô tả") or d(className="android.widget.EditText")
        if caption_box.exists(timeout=5):
            caption_box.click()
            time.sleep(0.5)
            # Gõ tiếng Việt chuẩn qua ADBKeyBoard
            self.adb.type_vietnamese_text(self.device_id, caption_text)
            time.sleep(1)

        # 7. Bấm nút ĐĂNG
        btn_publish = d(text="Đăng")
        if btn_publish.exists(timeout=5):
            btn_publish.click()
            print(f"[ShopeeAutomator] ✅ Đã bấm nút ĐĂNG thành công trên {self.device_id}!")
            time.sleep(12) # Chờ upload tiến độ 100%

            # Chụp ảnh màn hình làm bằng chứng
            if screenshot_path:
                self.adb.capture_screenshot(self.device_id, screenshot_path)

            return True

        return False
