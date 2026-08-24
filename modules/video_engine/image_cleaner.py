import io
import requests
from pathlib import Path
from typing import List
from PIL import Image, ImageOps
from loguru import logger

from config.settings import CLEANED_IMAGES_DIR

class ImageCleaner:
    """Tải và làm sạch ảnh sản phẩm (xóa phông, logo shop cũ)."""

    def __init__(self, output_dir: Path = CLEANED_IMAGES_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download_and_clean_images(self, item_id: str, image_urls: List[str], max_images: int = 4) -> List[str]:
        """Tải danh sách ảnh HD và lưu vào thư mục làm việc."""
        cleaned_paths = []
        item_folder = self.output_dir / f"item_{item_id}"
        item_folder.mkdir(parents=True, exist_ok=True)

        for idx, url in enumerate(image_urls[:max_images]):
            target_path = item_folder / f"image_{idx+1}.jpg"

            if target_path.exists():
                cleaned_paths.append(str(target_path))
                continue

            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                    # Tối ưu kích thước chuẩn nét
                    img = ImageOps.fit(img, (1080, 1080), Image.Resampling.LANCZOS)
                    img.save(target_path, "JPEG", quality=95)
                    cleaned_paths.append(str(target_path))
                else:
                    logger.warning(f"⚠️ Không tải được ảnh {url} (HTTP {resp.status_code})")
            except Exception as e:
                logger.error(f"❌ Lỗi xử lý ảnh {url}: {e}")

        return cleaned_paths
