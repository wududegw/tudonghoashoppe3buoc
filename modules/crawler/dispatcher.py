import json
from typing import Dict, Any, Optional
from config.settings import KOLS_CONFIG_PATH

class ProductDispatcher:
    """Điều hướng sản phẩm về đúng KOL phụ trách theo ngành hàng/từ khóa."""

    def __init__(self, config_path=KOLS_CONFIG_PATH):
        self.kols = []
        self.load_kols(config_path)

    def load_kols(self, config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.kols = data.get("kols", [])
        except Exception as e:
            print(f"[!] Lỗi tải kols_config.json: {e}")

    def assign_kol(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Gán KOL phù hợp nhất cho sản phẩm."""
        title = product.get("title", "").lower()
        category = product.get("category", "").lower()

        best_kol = None
        max_score = -1

        for kol in self.kols:
            score = 0
            for kw in kol.get("keywords", []):
                if kw.lower() in title:
                    score += 2
                if kw.lower() in category:
                    score += 1

            if score > max_score:
                max_score = score
                best_kol = kol

        if not best_kol or max_score <= 0:
            best_kol = self.kols[-1] if self.kols else {"kol_id": "kol_10", "name": "KOL Săn Sale"}

        return best_kol
