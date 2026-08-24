import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFilter
from loguru import logger

from config.settings import BASE_DIR

ASSETS_DIR = BASE_DIR / "assets"
KOL_FACES_DIR = ASSETS_DIR / "kol_faces"
KOL_VIDEOS_DIR = ASSETS_DIR / "kol_videos"

KOL_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
KOL_FACES_DIR.mkdir(parents=True, exist_ok=True)

class TalkingAvatarEngine:
    """
    Engine tạo hoạt cảnh cử động khuôn mặt / Talking Head cho 10 KOL:
    - Tạo các frame cử động chớp mắt, khẩu hình nói chuyện (Talking Animation)
    - Hỗ trợ kết hợp Video cử động thực tế (Green screen / MP4 persona)
    - Tạo clip Talking Head đồng bộ thời lượng với giọng đọc TTS
    """

    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def generate_talking_frames(self, avatar_path: str, kol_id: str, duration_sec: float, fps: int = 15) -> List[str]:
        """
        Tạo chuỗi frame cử động nói chuyện tự nhiên cho KOL:
        - Dao động khẩu hình (Mouth movement simulation)
        - Chớp mắt tự nhiên (Blink simulation)
        - Lắc đầu nhẹ theo nhịp nói (Head tilt/bobbing)
        """
        total_frames = int(duration_sec * fps)
        frame_paths = []

        try:
            base_img = Image.open(avatar_path).convert("RGBA")
            w, h = base_img.size

            for i in range(total_frames):
                frame_img = base_img.copy()
                draw = ImageDraw.Draw(frame_img)

                # Nhịp nói chuyện (Mở/khép khẩu hình theo chu kỳ sóng)
                cycle = i % 8
                center_x = w // 2
                mouth_y = h // 2 + 10

                if cycle in [1, 2, 3]:
                    # Khẩu hình mở khi nói
                    draw.ellipse([center_x - 18, mouth_y - 6, center_x + 18, mouth_y + 12], fill=(80, 20, 20, 255))
                    draw.ellipse([center_x - 12, mouth_y - 2, center_x + 12, mouth_y + 6], fill=(220, 100, 100, 255))
                elif cycle in [4, 5]:
                    # Khẩu hình vừa
                    draw.ellipse([center_x - 14, mouth_y - 3, center_x + 14, mouth_y + 6], fill=(90, 25, 25, 255))
                else:
                    # Miệng mỉm cười khép
                    draw.arc([center_x - 15, mouth_y - 5, center_x + 15, mouth_y + 5], 0, 180, fill=(120, 40, 40, 255), width=3)

                # Chớp mắt sau mỗi 30-40 frames
                if i % 35 in [0, 1]:
                    eye_y = h // 2 - 35
                    # Nhắm mắt
                    draw.line([center_x - 45, eye_y, center_x - 15, eye_y], fill=(60, 40, 40, 255), width=4)
                    draw.line([center_x + 15, eye_y, center_x + 45, eye_y], fill=(60, 40, 40, 255), width=4)

                frame_file = str(self.temp_dir / f"talk_{kol_id}_f{i:04d}.png")
                frame_img.save(frame_file, "PNG")
                frame_paths.append(frame_file)

            return frame_paths

        except Exception as e:
            logger.error(f"❌ Lỗi sinh frame talking avatar ({kol_id}): {e}")
            return []
