import json
import re
from typing import Dict, Any
from loguru import logger
import google.generativeai as genai

from config.settings import GEMINI_API_KEY

# Bộ lọc từ ngữ vi phạm chính sách kiểm duyệt video của Shopee / TikTok
BANNED_WORDS = [
    "cam kết 100%", "trị dứt điểm", "rẻ nhất thị trường", "số 1 việt nam",
    "chữa khỏi", "hàng đầu thế giới", "đảm bảo 100%", "tốt nhất hiện nay",
    "vĩnh viễn", "tuyệt đối"
]

class ScriptGenerator:
    """Sử dụng Gemini AI để tạo kịch bản video review ngắn chuẩn viral (Không đọc giá cứng, lọc từ cấm)."""

    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.api_key = api_key
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-1.5-flash")
            except Exception as e:
                logger.warning(f"⚠️ Không thể khởi tạo Gemini AI: {e}")
                self.model = None
        else:
            self.model = None
            logger.info("ℹ️ Chưa cấu hình GEMINI_API_KEY, hệ thống sẽ sử dụng kịch bản mẫu tối ưu sẵn.")

    def clean_banned_words(self, text: str) -> str:
        """Loại bỏ các từ ngữ vi phạm chính sách kiểm duyệt video."""
        cleaned = text
        for bw in BANNED_WORDS:
            cleaned = re.sub(re.escape(bw), "rất tốt", cleaned, flags=re.IGNORECASE)
        return cleaned

    def generate_script(self, product: Dict[str, Any], kol_info: Dict[str, Any]) -> Dict[str, str]:
        """
        Tạo kịch bản video review 12-15 giây theo công thức:
        - Hook (3s đầu): Thu hút chú ý theo đúng phong cách/giọng điệu KOL
        - Body (8s giữa): Nêu 1-2 công năng tiện ích đột phá, giải quyết vấn đề
        - CTA (4s cuối): Kêu gọi bấm vào giỏ hàng góc trái màn hình
        - TUYỆT ĐỐI KHÔNG ĐỌC GIÁ TIỀN CỤ THỂ để video không bị lỗi thời khi giá thay đổi
        """
        title = product.get("title", "")
        category = product.get("category", "")
        kol_style = kol_info.get("style", "Hào hứng, chia sẻ mẹo vặt gia đình")
        kol_name = kol_info.get("name", "KOL Shopee")
        hook_prefix = kol_info.get("hook_prefix", "Món đồ này đang cực hot trên Shopee!")

        if self.model:
            prompt = f"""
Bạn là KOL review '{kol_name}'. Phong cách của bạn: {kol_style}.
Câu mở đầu đặc trưng của bạn: "{hook_prefix}"

Hãy viết kịch bản video review ngắn (12-15 giây) cho sản phẩm sau:
- Tên sản phẩm: {title}
- Ngành hàng: {category}

QUY TẮC BẮT BUỘC:
1. TUYỆT ĐỐI KHÔNG ĐỌC HOẶC NÊU SỐ TIỀN/GIÁ CỤ THỂ (thay vào đó dùng "giá cực hạt dẻ", "đang có ưu đãi sâu trong giỏ hàng").
2. Độ dài phần đọc (full_voice_text) khoảng 35 - 45 từ tiếng Việt (đọc tự nhiên trong 12 - 15 giây).
3. Câu kết thúc (CTA) bắt buộc kêu gọi: "Mọi người bấm ngay vào giỏ hàng góc trái màn hình để xem chi tiết nhé!"
4. KHÔNG dùng các từ tâng bốc quá đà như: "cam kết 100%", "rẻ nhất", "chữa dứt điểm", "số 1".

Trả về DUY NHẤT 1 JSON object hợp lệ (không kèm markdown ngoài JSON):
{{
  "hook": "Câu mở đầu giật tít 3 giây đầu",
  "body": "Đoạn review công năng tiện ích nổi bật nhất",
  "cta": "Mọi người bấm ngay vào giỏ hàng góc trái màn hình để xem ưu đãi nhé!",
  "full_voice_text": "Toàn bộ lời đọc nối liền mạch (Hook + Body + CTA)",
  "caption": "Caption ngắn gọn cuốn hút kèm icon",
  "hashtags": "#ShopeeVideo #Review #GiaHot #GiaDung"
}}
"""
            try:
                response = self.model.generate_content(prompt)
                raw_text = response.text.strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text.replace("```json", "").replace("```", "").strip()
                elif raw_text.startswith("```"):
                    raw_text = raw_text.replace("```", "").strip()

                data = json.loads(raw_text)
                # Lọc từ cấm
                data["full_voice_text"] = self.clean_banned_words(data.get("full_voice_text", ""))
                data["body"] = self.clean_banned_words(data.get("body", ""))
                return data
            except Exception as e:
                logger.warning(f"⚠️ Lỗi khi gọi Gemini AI: {e}. Sử dụng kịch bản tối ưu dự phòng.")

        # Fallback template chất lượng cao theo ngành hàng
        short_title = title[:35] if len(title) > 35 else title
        hook = f"{hook_prefix} Ai mà ngờ món này lại tiện đến thế!"
        body = f"Sản phẩm {short_title} đang rất được ưa chuộng nhờ thiết kế thông minh, hoàn thiện tỉ mỉ và cực kỳ tiện ích cho cả nhà."
        cta = "Mọi người bấm ngay vào giỏ hàng góc trái màn hình để xem ưu đãi nhé!"
        full_text = f"{hook} {body} {cta}"
        caption = f"Món đồ siêu tiện ích nhất định phải có! 🔥 {short_title}"
        hashtags = "#ShopeeVideo #ReviewShopee #DealHot #GiaTot"

        return {
            "hook": hook,
            "body": body,
            "cta": cta,
            "full_voice_text": self.clean_banned_words(full_text),
            "caption": caption,
            "hashtags": hashtags
        }
