import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image, ImageDraw, ImageFont
from loguru import logger

from config.settings import BASE_DIR, KOLS_CONFIG_PATH

ASSETS_DIR = BASE_DIR / "assets"
KOL_FACES_DIR = ASSETS_DIR / "kol_faces"
KOL_VIDEOS_DIR = ASSETS_DIR / "kol_videos"

class KOLManager:
    """Quản lý 10 Profile KOL Reviewer độc quyền: khuôn mặt, tính cách, giọng đọc và clip cử động."""

    def __init__(self, config_path: Path = KOLS_CONFIG_PATH):
        self.config_path = config_path
        self.kols: List[Dict[str, Any]] = []
        KOL_FACES_DIR.mkdir(parents=True, exist_ok=True)
        KOL_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
        self.load_kols()
        self.ensure_all_kol_assets()

    def load_kols(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.kols = data.get("kols", [])
        except Exception as e:
            logger.error(f"❌ Lỗi tải danh sách KOL: {e}")

    def get_kol_by_id(self, kol_id: str) -> Optional[Dict[str, Any]]:
        for k in self.kols:
            if k.get("kol_id") == kol_id:
                return k
        return self.kols[0] if self.kols else None

    def ensure_all_kol_assets(self):
        """Đảm bảo sẵn sàng 10 Avatar và mẫu Reviewer Persona cho 10 KOL."""
        for kol in self.kols:
            kol_id = kol.get("kol_id")
            avatar_path = BASE_DIR / kol.get("avatar_file", f"assets/kol_faces/{kol_id}.png")
            if not avatar_path.exists():
                self._generate_kol_reviewer_avatar(kol, avatar_path)

    def _generate_kol_reviewer_avatar(self, kol: Dict[str, Any], output_path: Path):
        """Vẽ Avatar KOL Reviewer sắc nét (Hình ảnh đại diện người review thực tế)."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        size = 400
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Màu sắc chủ đạo của KOL
        hex_color = kol.get("badge_color", "#FF6B6B")
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        primary_color = (r, g, b, 255)
        skin_color = (255, 220, 190, 255) if kol.get("gender") == "female" else (240, 205, 175, 255)
        hair_color = (40, 25, 20, 255)

        # Vẽ viền ngoài phát sáng
        margin = 12
        draw.ellipse([margin, margin, size - margin, size - margin], fill=(255, 255, 255, 230), outline=primary_color, width=12)

        # Tóc sau (đối với nữ)
        if kol.get("gender") == "female":
            draw.chord([60, 80, size - 60, 360], 0, 360, fill=hair_color)

        # Cổ & Thân áo
        center_x = size // 2
        draw.rectangle([center_x - 30, 200, center_x + 30, 260], fill=skin_color)
        draw.chord([40, 230, size - 40, size + 120], 0, 360, fill=primary_color)

        # Khuôn mặt
        draw.ellipse([center_x - 65, 90, center_x + 65, 230], fill=skin_color)

        # Mắt & Lông mày
        eye_y = 150
        draw.ellipse([center_x - 38, eye_y, center_x - 22, eye_y + 12], fill=(30, 30, 30, 255))
        draw.ellipse([center_x + 22, eye_y, center_x + 38, eye_y + 12], fill=(30, 30, 30, 255))
        draw.line([center_x - 42, eye_y - 8, center_x - 18, eye_y - 12], fill=hair_color, width=3)
        draw.line([center_x + 18, eye_y - 12, center_x + 42, eye_y - 8], fill=hair_color, width=3)

        # Tóc mái phía trước
        draw.chord([center_x - 70, 75, center_x + 70, 150], 180, 360, fill=hair_color)

        # Miệng cười
        draw.arc([center_x - 18, 185, center_x + 18, 205], 0, 180, fill=(180, 50, 50, 255), width=4)

        # Huy hiệu "KOL REVIEWER"
        badge_h = 55
        badge_y = size - 75
        draw.rounded_rectangle([25, badge_y, size - 25, badge_y + badge_h], radius=16, fill=primary_color)
        name = kol.get("name", "KOL")
        draw.text((center_x, badge_y + badge_h // 2), f"🎙️ {name} Review", fill=(255, 255, 255), anchor="mm")

        img.save(output_path, "PNG")
        logger.info(f"🎨 Đã tạo Avatar Reviewer cho KOL {kol.get('name')} -> {output_path}")

    def get_kol_reviewer_video_clip(self, kol_id: str) -> Optional[str]:
        """Lấy file video clip người thật review nếu có (ví dụ kol_01_review.mp4)."""
        video_file = KOL_VIDEOS_DIR / f"{kol_id}_review.mp4"
        if video_file.exists():
            return str(video_file)
        return None
