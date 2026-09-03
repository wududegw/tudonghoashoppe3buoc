from typing import Dict, Any
from modules.crawler.dispatcher import ProductDispatcher

class ChannelDispatcher:
    """Wrapper điều hướng ngành hàng đồng bộ với ProductDispatcher và kols_config.json."""

    def __init__(self):
        self.dispatcher = ProductDispatcher()

    def dispatch_category(self, title: str, raw_category: str = "") -> str:
        dummy_product = {"title": title, "category": raw_category}
        kol = self.dispatcher.assign_kol(dummy_product)
        return kol.get("category", "Gia dụng & Đời sống")

    def get_kol_profile(self, category_key: str) -> Dict[str, Any]:
        dummy_product = {"title": category_key, "category": category_key}
        return self.dispatcher.assign_kol(dummy_product)
