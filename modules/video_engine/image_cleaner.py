import io
import os
import requests
from PIL import Image, ImageOps, ImageFilter
from pathlib import Path

try:
    from rembg import remove as remove_bg
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

class ImageCleaner:
    def __init__(self, output_size=(1080, 1920)):
        self.output_size = output_size

    def download_image(self, url: str) -> Image.Image:
        """Tải ảnh gốc từ link CDN Shopee"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        return Image.open(io.BytesIO(res.content)).convert("RGBA")

    def clean_and_recontextualize(self, raw_img: Image.Image, bg_color=(245, 245, 250)) -> Image.Image:
        """
        1. Xóa phông/chữ cũ/watermark bằng AI (rembg)
        2. Đặt vào canvas Studio 9:16 với nền hiện đại và bóng đổ tự nhiên
        """
        canvas = Image.new("RGBA", self.output_size, bg_color + (255,))

        if REMBG_AVAILABLE:
            try:
                # Xóa sạch nền cũ và logo/khung sale
                clean_fg = remove_bg(raw_img)
            except Exception as e:
                print(f"[ImageCleaner] Lỗi rembg, dùng ảnh gốc: {e}")
                clean_fg = raw_img
        else:
            clean_fg = raw_img

        # Resize vật thể vừa vặn khung hình (chiếm 65% chiều rộng canvas)
        target_w = int(self.output_size[0] * 0.75)
        aspect_ratio = clean_fg.height / clean_fg.width
        target_h = int(target_w * aspect_ratio)

        if target_h > int(self.output_size[1] * 0.55):
            target_h = int(self.output_size[1] * 0.55)
            target_w = int(target_h / aspect_ratio)

        resized_fg = clean_fg.resize((target_w, target_h), Image.LANCZOS)

        # Tính toạ độ căn giữa theo chiều ngang, hơi cao hơn giữa theo chiều dọc
        pos_x = (self.output_size[0] - target_w) // 2
        pos_y = (self.output_size[1] - target_h) // 2 - 50

        # Tạo bóng đổ mềm (Drop Shadow) cho sản phẩm trông như ở Studio 3D
        shadow = Image.new("RGBA", (target_w + 40, target_h + 40), (0, 0, 0, 0))
        shadow_mask = resized_fg.split()[3].filter(ImageFilter.GaussianBlur(15))
        shadow.paste((30, 30, 30, 90), (20, 20), mask=shadow_mask)

        # Ghép bóng và sản phẩm vào canvas
        canvas.paste(shadow, (pos_x - 20, pos_y - 10), shadow)
        canvas.paste(resized_fg, (pos_x, pos_y), resized_fg)

        return canvas.convert("RGB")

    def process_product_images(self, image_urls: list, output_folder: Path) -> list:
        """Xử lý danh sách ảnh sản phẩm và lưu ra folder tạm"""
        output_folder.mkdir(parents=True, exist_ok=True)
        clean_paths = []

        # Lấy tối đa 4 ảnh chất lượng nhất
        for idx, url in enumerate(image_urls[:4]):
            try:
                raw = self.download_image(url)
                clean_img = self.clean_and_recontextualize(raw)
                save_path = output_folder / f"clean_img_{idx + 1}.jpg"
                clean_img.save(save_path, quality=95)
                clean_paths.append(str(save_path))
            except Exception as e:
                print(f"[ImageCleaner] Lỗi xử lý ảnh {url}: {e}")

        return clean_paths
