import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from loguru import logger

from config.settings import VIDEOS_DIR, TEMP_DIR, VIDEO_CONFIG, BASE_DIR
from modules.video_engine.kol_manager import KOLManager
from modules.video_engine.talking_avatar import TalkingAvatarEngine

class VideoComposer:
    """
    Dựng Video Review Shopee chuẩn phong cách KOL (Bố cục tối giản, tôn trọn vẹn sản phẩm):
    - Khung hình dọc 9:16 (1080x1920)
    - Người Reviewer (KOL Talking Head) & Kênh ở góc trên
    - Trọn vẹn không gian trung tâm cho hình ảnh sản phẩm HD phóng to
    - Chân video duy nhất nút: "👇 BẤM VÀO GIỎ HÀNG GÓC TRÁI ĐỂ XEM 👇"
    """

    def __init__(self, output_dir: Path = VIDEOS_DIR, temp_dir: Path = TEMP_DIR):
        self.output_dir = output_dir
        self.temp_dir = temp_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.kol_mgr = KOLManager()
        self.talking_engine = TalkingAvatarEngine(self.temp_dir)

    def prepare_review_frame(
        self,
        img_path: str,
        kol_info: Dict[str, Any],
        title: str,
        index: int
    ) -> str:
        """Tạo khung hình video review tối giản (Đã bỏ thanh tên sản phẩm)."""
        framed_output = str(self.temp_dir / f"review_frame_{kol_info.get('kol_id')}_{index}.png")

        w, h = VIDEO_CONFIG["width"], VIDEO_CONFIG["height"]
        canvas = Image.new("RGBA", (w, h), (15, 15, 20, 255))

        # 1. Background mờ nghệ thuật từ ảnh sản phẩm
        try:
            prod_img = Image.open(img_path).convert("RGBA")
            bg_blurred = prod_img.resize((w, h), Image.Resampling.BILINEAR).filter(ImageFilter.GaussianBlur(radius=35))
            dimmer = Image.new("RGBA", (w, h), (0, 0, 0, 175))
            bg_blurred.paste(dimmer, (0, 0), dimmer)
            canvas.paste(bg_blurred, (0, 0))
        except Exception as e:
            logger.warning(f"Lỗi tạo background: {e}")

        # 2. Hiển thị ảnh sản phẩm trọn vẹn ở giữa màn hình (Không bị thanh tiêu đề che)
        try:
            prod_img = Image.open(img_path).convert("RGBA")
            main_w = 960
            ratio = main_w / prod_img.width
            main_h = int(prod_img.height * ratio)
            if main_h > 1200:
                main_h = 1200
                main_w = int(prod_img.width * (1200 / prod_img.height))
            prod_resized = prod_img.resize((main_w, main_h), Image.Resampling.LANCZOS)
            pos_x = (w - main_w) // 2
            pos_y = (h - main_h) // 2 + 20
            canvas.paste(prod_resized, (pos_x, pos_y), prod_resized)
        except Exception as e:
            logger.error(f"Lỗi đặt ảnh chính: {e}")

        # 3. Chèn KOL Reviewer Talking Head ở góc trên bên trái
        kol_id = kol_info.get("kol_id")
        avatar_path = BASE_DIR / kol_info.get("avatar_file", f"assets/kol_faces/{kol_id}.png")
        if avatar_path.exists():
            try:
                avatar_img = Image.open(avatar_path).convert("RGBA")
                # Kích thước khung reviewer (210x210)
                avatar_img = avatar_img.resize((210, 210), Image.Resampling.LANCZOS)
                canvas.paste(avatar_img, (45, 65), avatar_img)
            except Exception as e:
                logger.error(f"Lỗi paste avatar KOL: {e}")

        # 4. Vẽ Header & Thông tin kênh KOL Review
        draw = ImageDraw.Draw(canvas)
        hex_color = kol_info.get("badge_color", "#FF6B6B")
        r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
        primary_color = (r, g, b, 255)

        # Header Box bên cạnh avatar
        draw.rounded_rectangle([270, 75, w - 45, 175], radius=18, fill=(0, 0, 0, 210), outline=primary_color, width=3)
        draw.text((295, 102), f"🎙️ {kol_info.get('full_title', kol_info.get('name'))}", fill=(255, 215, 0), anchor="la")
        draw.text((295, 140), f"Chuyên mục: {kol_info.get('category')}", fill=(220, 220, 220), anchor="la")

        # 5. Footer DUY NHẤT: BẤM VÀO GIỎ HÀNG GÓC TRÁI ĐỂ XEM
        footer_y = h - 230
        draw.rounded_rectangle([60, footer_y, w - 60, footer_y + 90], radius=22, fill=primary_color, outline=(255, 255, 255, 230), width=3)
        draw.text((w // 2, footer_y + 45), "👇 BẤM VÀO GIỎ HÀNG GÓC TRÁI ĐỂ XEM 👇", fill=(255, 255, 255), anchor="mm")

        canvas.convert("RGB").save(framed_output, "PNG")
        return framed_output

    def create_video_from_images(
        self,
        item_id: str,
        image_paths: List[str],
        audio_path: str,
        title: str,
        kol_info: Dict[str, Any],
        hook_text: str = ""
    ) -> str:
        """Render trọn bộ video review có KOL lồng tiếng và xuất hiện trực tiếp."""
        kol_id = kol_info.get("kol_id", "kol_01")
        output_video = str(self.output_dir / f"video_{kol_id}_{item_id}.mp4")

        try:
            from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

            audio_clip = AudioFileClip(audio_path)
            total_duration = audio_clip.duration

            if not image_paths:
                raise ValueError("Không có hình ảnh sản phẩm để dựng video")

            duration_per_img = total_duration / len(image_paths)

            framed_images = []
            for idx, img_p in enumerate(image_paths):
                f_path = self.prepare_review_frame(img_p, kol_info, title, idx)
                framed_images.append(f_path)

            clips = []
            for f_path in framed_images:
                clip = ImageClip(f_path).set_duration(duration_per_img)
                clips.append(clip)

            final_video = concatenate_videoclips(clips, method="compose")
            final_video = final_video.set_audio(audio_clip)

            final_video.write_videofile(
                output_video,
                fps=VIDEO_CONFIG["fps"],
                codec="libx264",
                audio_codec="aac",
                threads=4,
                logger=None
            )

            final_video.close()
            audio_clip.close()

            logger.success(f"🎬 [VideoComposer] Đã render video Review cho KOL {kol_info.get('name')}: {output_video}")
            return output_video

        except Exception as e:
            logger.error(f"❌ [VideoComposer] Lỗi render video: {e}")
            return ""
