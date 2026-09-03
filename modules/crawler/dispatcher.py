import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger
from config.settings import KOLS_CONFIG_PATH

class ProductDispatcher:
    """Điều hướng sản phẩm về đúng 1 trong 10 KOL phụ trách theo ngành hàng/từ khóa."""

    def __init__(self, config_path: Path = KOLS_CONFIG_PATH):
        self.config_path = config_path
        self.kols: List[Dict[str, Any]] = []
        self.load_kols(config_path)

    def load_kols(self, config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.kols = data.get("kols", [])
        except Exception as e:
            logger.error(f"❌ Lỗi tải kols_config.json: {e}")

    def assign_kol(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phân tích tiêu đề và ngành hàng của sản phẩm để gán KOL tối ưu nhất.
        Áp dụng thuật toán tính trọng số từ khóa:
        - Từ khóa xuất hiện trong Tiêu đề: +3 điểm
        - Từ khóa xuất hiện trong Danh mục: +2 điểm
        """
        title = product.get("title", "").lower()
        category = product.get("category", "").lower()

        best_kol = None
        max_score = -1

        for kol in self.kols:
            score = 0
            keywords = kol.get("keywords", [])
            for kw in keywords:
                kw_lower = kw.lower()
                if kw_lower in title:
                    score += 3
                if kw_lower in category:
                    score += 2

            if score > max_score:
                max_score = score
                best_kol = kol

        # Nếu không khớp từ khóa cụ thể nào, fallback về KOL 10 (Săn Deal Hot) hoặc KOL 01 (Gia Dụng)
        if not best_kol or max_score <= 0:
            best_kol = self.kols[-1] if self.kols else {
                "kol_id": "kol_10",
                "name": "Linh Chi",
                "full_title": "Linh Chi - Thánh Săn Deal 1K",
                "category": "Deal Hời & Độc Lạ",
                "voice": "vi-VN-HoaiMyNeural",
                "device_id": "emulator-5572",
                "badge_color": "#E53E3E"
            }

        return best_kol
