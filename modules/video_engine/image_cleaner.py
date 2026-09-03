import io
import requests
from pathlib import Path
from typing import List
from PIL import Image, ImageOps
from loguru import logger

from config.settings import CLEANED_IMAGES_DIR

class ImageCleaner:
    """Tải và xử lý chuẩn hóa ảnh sản phẩm HD phục vụ dựng video."""

    def __init__(self, output_dir: Path = CLEANED_IMAGES_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download_and_clean_images(self, item_id: str, image_urls: List[str], max_images: int = 4) -> List[str]:
        """Tải danh sách ảnh HD, căn chỉnh tỷ lệ sắc nét 1080x1080."""
        cleaned_paths = []
        item_folder = self.output_dir / f"item_{item_id}"
        item_folder.mkdir(parents=True, exist_ok=True)

        valid_urls = [u for u in image_urls if u and u.startswith("http")][:max_images]
        if not valid_urls:
            # Fallback tạo 1 ảnh mẫu nếu không có ảnh nào
            fallback_img_path = item_folder / "image_1.jpg"
            if not fallback_img_path.exists():
                img = Image.new("RGB", (1080, 1080), (240, 242, 245))
                img.save(fallback_img_path, "JPEG", quality=90)
            return [str(fallback_img_path)]

        for idx, url in enumerate(valid_urls):
            target_path = item_folder / f"image_{idx+1}.jpg"

            if target_path.exists() and target_path.stat().st_size > 1000:
                cleaned_paths.append(str(target_path))
                continue

            try:
                resp = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                    # Chuẩn hóa kích thước 1080x1080 giữ đúng tỷ lệ không bị méo hình
                    img = ImageOps.fit(img, (1080, 1080), Image.Resampling.LANCZOS)
                    img.save(target_path, "JPEG", quality=95)
                    cleaned_paths.append(str(target_path))
                else:
                    logger.warning(f"⚠️ Không tải được ảnh #{idx+1} {url[:50]} (HTTP {resp.status_code})")
            except Exception as e:
                logger.error(f"❌ Lỗi tải ảnh sản phẩm: {e}")

        # Nếu không tải được cái nào, tạo 1 ảnh fallback
        if not cleaned_paths:
            fallback_path = item_folder / "fallback.jpg"
            img = Image.new("RGB", (1080, 1080), (245, 245, 245))
            img.save(fallback_path, "JPEG")
            cleaned_paths.append(str(fallback_path))

        return cleaned_paths

    def process_product_images(self, image_urls: List[str], target_dir: Path) -> List[str]:
        """Hỗ trợ tương thích ngược cho webhook/api_server."""
        target_dir.mkdir(parents=True, exist_ok=True)
        return self.download_and_clean_images(item_id=target_dir.name, image_urls=image_urls)
