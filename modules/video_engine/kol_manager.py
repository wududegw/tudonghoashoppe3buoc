import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

from config.settings import BASE_DIR, KOLS_CONFIG_PATH, KOL_FACES_DIR

class KOLManager:
    """Quản lý 10 Profile KOL Reviewer độc quyền: khuôn mặt, tính cách, giọng đọc và thiết bị phụ trách."""

    def __init__(self, config_path: Path = KOLS_CONFIG_PATH):
        self.config_path = config_path
        self.kols: List[Dict[str, Any]] = []
        KOL_FACES_DIR.mkdir(parents=True, exist_ok=True)
        self.load_kols()
        self.ensure_all_kol_assets()

    def load_kols(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.kols = data.get("kols", [])
        except Exception as e:
            logger.error(f"❌ Lỗi tải danh sách KOL từ {self.config_path}: {e}")

    def get_kol_by_id(self, kol_id: str) -> Dict[str, Any]:
        """Lấy profile của KOL theo mã định danh."""
        for k in self.kols:
            if k.get("kol_id") == kol_id:
                return k
        return self.kols[0] if self.kols else {
            "kol_id": "kol_01",
            "name": "Hoàng Yến",
            "full_title": "Hoàng Yến - Gia Dụng Tiện Ích",
            "category": "Gia dụng & Đời sống",
            "avatar_file": "assets/kol_faces/kol_01.png",
            "voice": "vi-VN-HoaiMyNeural",
            "device_id": "emulator-5554",
            "badge_color": "#FF6B6B"
        }

    def ensure_all_kol_assets(self):
        """Đảm bảo sẵn sàng 10 Avatar cho 10 KOL."""
        for kol in self.kols:
            kol_id = kol.get("kol_id", "kol_01")
            avatar_path = BASE_DIR / kol.get("avatar_file", f"assets/kol_faces/{kol_id}.png")
            if not avatar_path.exists():
                # Nếu chưa có file, thử lấy từ kol_01.png
                default_avatar = KOL_FACES_DIR / "kol_01.png"
                if default_avatar.exists():
                    import shutil
                    shutil.copy(default_avatar, avatar_path)
                    logger.info(f"🎨 Khởi tạo avatar cho {kol_id}: {avatar_path.name}")
