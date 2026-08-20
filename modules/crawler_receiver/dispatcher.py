import json
from pathlib import Path

class ChannelDispatcher:
    def __init__(self, config_path: str = None):
        if not config_path:
            config_path = Path(__file__).parent.parent.parent / "config" / "kols_config.json"
        
        with open(config_path, "r", encoding="utf-8") as f:
            self.kols_config = json.load(f)

        # Bộ từ khóa nhận diện ngành hàng
        self.keywords_map = {
            "GIA_DUNG": ["quạt", "bếp", "nồi", "máy xay", "hút bụi", "tiện ích", "nhà cửa", "chảo", "đèn pin"],
            "THOI_TRANG_NU": ["váy", "đầm", "áo nữ", "chân váy", "set đồ nữ", "croptop", "bikini", "yếm"],
            "THOI_TRANG_NAM": ["polo", "áo nam", "quần âu", "quần jean nam", "sơ mi nam", "ví da", "thắt lưng"],
            "CONG_NGHE": ["tai nghe", "củ sạc", "cáp sạc", "bàn phím", "chuột", "loa bluetooth", "pin dự phòng"],
            "MY_PHAM": ["son", "kem chống nắng", "serum", "sữa rửa mặt", "toner", "mặt nạ", "cushion"],
            "ME_BE": ["bỉm", "tã", "sữa", "đồ chơi trẻ em", "bình sữa", "xe đẩy", "quần áo bé"],
            "AN_VAT": ["bánh tráng", "khô bò", "khô gà", "cơm cháy", "mực rim", "ô mai", "hạt điều"],
            "DECOR": ["đèn led", "tranh", "thảm", "gối", "đồng hồ treo tường", "hoa giả", "kệ gỗ"],
            "THE_THAO": ["bình giữ nhiệt", "thảm yoga", "quần gym", "găng tay", "vợt", "dây kháng lực"],
            "XE_CO": ["giá đỡ điện thoại xe", "gương xe", "mũ bảo hiểm", "nhớt", "bạt phủ xe", "áo mưa"]
        }

    def dispatch_category(self, title: str, raw_category: str = "") -> str:
        """Phân loại sản phẩm về đúng 1 trong 10 kênh KOL"""
        text = f"{title} {raw_category}".lower()

        # So khớp từ khóa
        for category, keywords in self.keywords_map.items():
            for kw in keywords:
                if kw in text:
                    return category

        # Mặc định về Gia Dụng nếu không khớp ngành hàng đặc thù
        return "GIA_DUNG"

    def get_kol_profile(self, category_key: str) -> dict:
        """Lấy thông tin cấu hình của KOL đại diện cho ngành hàng đó"""
        return self.kols_config.get(category_key, self.kols_config["GIA_DUNG"])
