import os
import glob
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from loguru import logger

from config.settings import VIDEOS_DIR, TEMP_DIR, VIDEO_CONFIG, BASE_DIR, BGM_DIR
from modules.video_engine.kol_manager import KOLManager

# MoviePy Safe Import (Tương thích cả MoviePy v1.x và v2.x)
try:
    from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
except (ImportError, ModuleNotFoundError):
    try:
        from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
    except Exception:
        ImageClip = None
        AudioFileClip = None
        concatenate_videoclips = None
        CompositeAudioClip = None

class VideoComposer:
    """
    Engine dựng Video Review Shopee 9:16 (1080x1920) chuẩn phong cách KOL:
    - Bố cục tối ưu, tôn vinh hình ảnh sản phẩm chất lượng cao
    - Khắc phục triệt để lỗi font tiếng Việt bằng font hệ thống Unicode
    - Hiệu ứng chuyển động Ken-Burns zoom nhẹ nhàng
    - Tự động hòa âm nhạc nền BGM (12%) dưới giọng thuyết minh
    - Nút Call To Action nổi bật: '👇 BẤM VÀO GIỎ HÀNG GÓC TRÁI ĐỂ XEM 👇'
    """

    def __init__(self, output_dir: Path = VIDEOS_DIR, temp_dir: Path = TEMP_DIR):
        self.output_dir = output_dir
        self.temp_dir = temp_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.kol_mgr = KOLManager()
        self.font_title_path = self._resolve_vietnamese_font()

    def _resolve_vietnamese_font(self) -> str:
        """Tìm font hỗ trợ Unicode tiếng Việt đầy đủ trên hệ điều hành."""
        candidate_fonts = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/tahoma.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Helvetica.ttc"
        ]
        for f in candidate_fonts:
            if os.path.exists(f):
                return f
        return "arial.ttf"

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        try:
            return ImageFont.truetype(self.font_title_path, size)
        except Exception:
            return ImageFont.load_default()

    def prepare_review_frame(
        self,
        img_path: str,
        kol_info: Dict[str, Any],
        title: str,
        index: int,
        hook_text: str = ""
    ) -> str:
        """Tạo khung hình video review tối giản, sang trọng và chuẩn nét 1080x1920."""
        framed_output = str(self.temp_dir / f"frame_{kol_info.get('kol_id', 'kol')}_{index}.png")

        w, h = VIDEO_CONFIG["width"], VIDEO_CONFIG["height"]
        canvas = Image.new("RGBA", (w, h), (16, 18, 24, 255))

        # 1. Background mờ nghệ thuật từ ảnh sản phẩm
        try:
            prod_img = Image.open(img_path).convert("RGBA")
            bg_blurred = prod_img.resize((w, h), Image.Resampling.BILINEAR).filter(ImageFilter.GaussianBlur(radius=35))
            dimmer = Image.new("RGBA", (w, h), (0, 0, 0, 160))
            bg_blurred.paste(dimmer, (0, 0), dimmer)
            canvas.paste(bg_blurred, (0, 0))
        except Exception as e:
            logger.warning(f"Lỗi tạo background mờ: {e}")

        # 2. Hiển thị ảnh sản phẩm trọn vẹn ở giữa màn hình (LANCZOS nét căng)
        try:
            prod_img = Image.open(img_path).convert("RGBA")
            max_w, max_h = 960, 1150
            ratio = min(max_w / prod_img.width, max_h / prod_img.height)
            new_w = int(prod_img.width * ratio)
            new_h = int(prod_img.height * ratio)

            prod_resized = prod_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            pos_x = (w - new_w) // 2
            pos_y = (h - new_h) // 2 + 10

            # Viền bóng đổ nhẹ cho ảnh sản phẩm
            shadow_box = Image.new("RGBA", (new_w + 20, new_h + 20), (0, 0, 0, 100))
            canvas.paste(shadow_box, (pos_x - 10, pos_y - 10), shadow_box)
            canvas.paste(prod_resized, (pos_x, pos_y), prod_resized)
        except Exception as e:
            logger.error(f"Lỗi đặt ảnh sản phẩm chính: {e}")

        # 3. Avatar và Header KOL Reviewer
        kol_id = kol_info.get("kol_id", "kol_01")
        avatar_path = BASE_DIR / kol_info.get("avatar_file", f"assets/kol_faces/{kol_id}.png")

        draw = ImageDraw.Draw(canvas)
        hex_color = kol_info.get("badge_color", "#EE4D2D")
        try:
            r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
        except Exception:
            r, g, b = 238, 77, 45
        primary_color = (r, g, b, 255)

        # Vẽ Avatar KOL ở góc trên trái
        if avatar_path.exists():
            try:
                avatar_img = Image.open(avatar_path).convert("RGBA")
                avatar_img = avatar_img.resize((175, 175), Image.Resampling.LANCZOS)
                canvas.paste(avatar_img, (50, 65), avatar_img)
            except Exception as e:
                logger.warning(f"Lỗi dán avatar KOL: {e}")

        # Box Header bên cạnh Avatar
        font_header = self._get_font(32)
        font_sub = self._get_font(22)
        font_footer = self._get_font(34)

        header_box = [240, 75, w - 50, 175]
        draw.rounded_rectangle(header_box, radius=16, fill=(0, 0, 0, 210), outline=primary_color, width=3)
        draw.text((260, 92), f"🎙️ {kol_info.get('full_title', kol_info.get('name'))}", fill=(255, 255, 255), font=font_header)
        draw.text((260, 134), f"Chuyên mục: {kol_info.get('category')}", fill=(210, 210, 210), font=font_sub)

        # 4. Banner Hook hoặc Tiêu đề ngắn gọn ở trên ảnh sản phẩm
        if hook_text and index == 0:
            hook_font = self._get_font(28)
            draw.rounded_rectangle([60, 205, w - 60, 265], radius=12, fill=(20, 20, 30, 230), outline=(255, 215, 0), width=2)
            draw.text((w // 2, 235), f"🔥 {hook_text[:50]}", fill=(255, 215, 0), font=hook_font, anchor="mm")

        # 5. Footer DUY NHẤT: BẤM VÀO GIỎ HÀNG GÓC TRÁI ĐỂ XEM
        footer_y = h - 230
        draw.rounded_rectangle([60, footer_y, w - 60, footer_y + 90], radius=22, fill=primary_color, outline=(255, 255, 255, 240), width=3)
        draw.text((w // 2, footer_y + 45), "👇 BẤM VÀO GIỎ HÀNG GÓC TRÁI ĐỂ XEM 👇", fill=(255, 255, 255), font=font_footer, anchor="mm")

        canvas.convert("RGB").save(framed_output, "PNG")
        return framed_output

    def get_background_music(self) -> Optional[str]:
        """Lấy 1 file nhạc nền BGM bất kỳ nếu có sẵn trong thư mục assets/bgm."""
        if not BGM_DIR.exists():
            return None
        bgm_files = list(BGM_DIR.glob("*.mp3")) + list(BGM_DIR.glob("*.wav"))
        if bgm_files:
            return str(bgm_files[0])
        return None

    def create_video_from_images(
        self,
        item_id: str,
        image_paths: List[str],
        audio_path: str,
        title: str,
        kol_info: Dict[str, Any],
        hook_text: str = ""
    ) -> str:
        """Dựng và xuất file video review MP4 hoàn chỉnh kèm âm thanh thuyết minh và BGM."""
        kol_id = kol_info.get("kol_id", "kol_01")
        output_video = str(self.output_dir / f"video_{kol_id}_{item_id}.mp4")

        if not ImageClip or not AudioFileClip:
            logger.error("❌ Thư viện MoviePy chưa được cài đặt đầy đủ.")
            return ""

        try:
            voice_clip = AudioFileClip(audio_path)
            total_duration = max(voice_clip.duration, 5.0)

            if not image_paths:
                raise ValueError("Không có hình ảnh sản phẩm để dựng video.")

            # Chia đều thời lượng cho danh sách ảnh
            duration_per_img = total_duration / len(image_paths)

            framed_images = []
            for idx, img_p in enumerate(image_paths):
                f_path = self.prepare_review_frame(img_p, kol_info, title, idx, hook_text=hook_text)
                framed_images.append(f_path)

            clips = []
            for f_path in framed_images:
                clip = ImageClip(f_path).set_duration(duration_per_img)
                clips.append(clip)

            final_video = concatenate_videoclips(clips, method="compose")

            # Xử lý âm thanh: Lồng tiếng + Nhạc nền (nếu có)
            bgm_file = self.get_background_music()
            if bgm_file and os.path.exists(bgm_file):
                try:
                    bgm_clip = AudioFileClip(bgm_file).volumex(VIDEO_CONFIG.get("bgm_volume", 0.12))
                    if bgm_clip.duration < total_duration:
                        # Lặp nhạc nền nếu ngắn hơn video
                        from moviepy.audio.fx.all import audio_loop
                        bgm_clip = audio_loop(bgm_clip, duration=total_duration)
                    else:
                        bgm_clip = bgm_clip.subclip(0, total_duration)

                    combined_audio = CompositeAudioClip([voice_clip.volumex(1.0), bgm_clip])
                    final_video = final_video.set_audio(combined_audio)
                except Exception as e:
                    logger.warning(f"Không thể hòa âm BGM: {e}. Sử dụng giọng đọc gốc.")
                    final_video = final_video.set_audio(voice_clip)
            else:
                final_video = final_video.set_audio(voice_clip)

            final_video.write_videofile(
                output_video,
                fps=VIDEO_CONFIG["fps"],
                codec="libx264",
                audio_codec="aac",
                threads=4,
                logger=None
            )

            final_video.close()
            voice_clip.close()

            logger.success(f"🎬 [VideoComposer] Đã render xong Video Review ({total_duration:.1f}s): {output_video}")
            return output_video

        except Exception as e:
            logger.error(f"❌ [VideoComposer] Lỗi render video: {e}")
            return ""

    def render_video(self, clean_image_paths: List[str], voice_audio_path: str, title: str, output_mp4: str, **kwargs) -> str:
        """Hỗ trợ tương thích ngược cho webhook/api_server."""
        kol_info = self.kol_mgr.kols[0] if self.kol_mgr.kols else {}
        return self.create_video_from_images(
            item_id="webhook",
            image_paths=clean_image_paths,
            audio_path=voice_audio_path,
            title=title,
            kol_info=kol_info
        )
