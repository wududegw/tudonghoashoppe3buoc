import json
import os
import google.generativeai as genai
from config.settings import GEMINI_API_KEY

class ScriptGenerator:
    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.api_key = api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.model = None

    def generate_script(self, title: str, price: str, original_price: str, 
                        kol_name: str, tone: str, category: str, default_hashtags: list) -> dict:
        """Sinh kịch bản video bán hàng và caption tối ưu theo Persona của KOL"""
        
        prompt = f"""
        Bạn là {kol_name}, một reviewer/KOC nổi tiếng trên Shopee Video.
        Phong cách của bạn: {tone}.
        
        Hãy viết kịch bản video ngắn (15-18 giây, tối đa 40-50 từ tiếng Việt) và caption đăng bài cho sản phẩm sau:
        - Tên sản phẩm: {title}
        - Giá bán hiện tại: {price}
        - Giá gốc: {original_price}
        - Ngành hàng: {category}
        
        Yêu cầu cấu trúc kịch bản:
        1. Câu Hook (3s đầu): Gây sốc, đánh vào tò mò hoặc vấn đề của người xem.
        2. Thân bài (10s): 1-2 điểm ăn tiền nhất của sản phẩm và mức giá sale cực hời.
        3. Kêu gọi hành động CTA (3s): Kêu gọi bấm vào giỏ hàng màu cam ở góc trái màn hình.
        
        Trả về kết quả DUY NHẤT dưới dạng JSON với cấu trúc:
        {{
            "hook": "Câu mở đầu giật tít",
            "body": "Đặc điểm nổi bật và mức giá",
            "cta": "Bấm ngay vào giỏ hàng góc trái săn sale nhé!",
            "voiceover_text": "Toàn bộ kịch bản đọc liền mạch từ Hook đến CTA (khoảng 35-45 từ)",
            "caption": "Câu tiêu đề caption ngắn kèm lời kêu gọi",
            "hashtags": ["#tag1", "#tag2", "#tag3", "#shopeevideo"]
        }}
        """
        
        if self.model:
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                data = json.loads(response.text.strip())
                return data
            except Exception as e:
                print(f"[ScriptGenerator] Lỗi Gemini API: {e}. Sử dụng kịch bản dự phòng...")

        # Fallback nếu chưa cấu hình Gemini API Key
        voiceover = f"Mọi người ơi, {title} đang sale cực sốc chỉ còn {price}! Mẫu này cực kỳ tiện lợi và bền đẹp. Số lượng có hạn, bấm vào giỏ hàng góc trái săn ngay nhé!"
        caption = f"🔥 DEAL HOT: {title} sale chỉ {price}! 👉 Bấm góc trái mua ngay"
        tags = default_hashtags + ["#shopeevideo", "#sansaleshopee"]
        
        return {
            "hook": f"Deal hời cho mọi người hôm nay nè!",
            "body": f"{title} giá chỉ còn {price}, chất lượng cực đỉnh.",
            "cta": "Bấm vào giỏ hàng góc trái săn ngay nhé!",
            "voiceover_text": voiceover,
            "caption": caption,
            "hashtags": tags
        }
