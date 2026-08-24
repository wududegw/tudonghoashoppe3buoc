import json
from typing import Dict, Any
from loguru import logger
import google.generativeai as genai

from config.settings import GEMINI_API_KEY

class ScriptGenerator:
    """Sử dụng Gemini AI để tạo kịch bản video review ngắn, caption & hashtags (Không đọc giá cứng)."""

    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.api_key = api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.model = None
            logger.warning("⚠️ Chưa cấu hình GEMINI_API_KEY, sẽ sử dụng kịch bản mẫu dự phòng.")

    def generate_script(self, product: Dict[str, Any], kol_info: Dict[str, Any]) -> Dict[str, str]:
        """Tạo kịch bản giật tít, review 15s tập trung công năng và CTA mua hàng (Không đề cập số tiền cụ thể)."""
        title = product.get("title", "")
        kol_style = kol_info.get("style", "Hào hứng, chia sẻ mẹo vặt gia đình")
        kol_name = kol_info.get("name", "KOL Shopee")
        hook_prefix = kol_info.get("hook_prefix", "Món đồ này đang cực hot trên Shopee!")

        if self.model:
            prompt = f"""
Bạn là KOL review '{kol_name}'. Phong cách của bạn: {kol_style}.
Câu mở đầu đặc trưng của bạn: "{hook_prefix}"

Hãy viết kịch bản review ngắn gọn cho sản phẩm sau:
- Tên sản phẩm: {title}

LƯU Ý QUAN TRỌNG: TUYỆT ĐỐI KHÔNG ĐỌC HOẶC NÊU SỐ TIỀN/GIÁ CỤ THỂ (để tránh video bị lỗi thời khi giá thay đổi). Thay vào đó hãy nhấn mạnh "giá cực hời", "đang có ưu đãi sốc trong giỏ hàng".

Yêu cầu trả về duy nhất 1 JSON object hợp lệ (không thêm markdown ngoài JSON):
{{
  "hook": "Câu mở đầu giật tít thu hút 3 giây đầu mang phong cách của bạn",
  "body": "Đoạn thuyết minh review công năng nổi bật và trải nghiệm thực tế (khoảng 35-45 từ, đọc trong 12-15s)",
  "cta": "Câu kêu gọi hành động: Mọi người bấm ngay vào giỏ hàng hoặc link bên dưới góc trái màn hình để săn deal ưu đãi hôm nay nhé!",
  "full_voice_text": "Toàn bộ lời đọc (ghép hook + body + cta)",
  "caption": "Đoạn caption ngắn gọn cuốn hút để đăng bài",
  "hashtags": "#ShopeeVideo #Review #DealHot #GiaTot"
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
                return data
            except Exception as e:
                logger.error(f"❌ Lỗi gọi Gemini AI: {e}. Chuyển sang kịch bản mặc định.")

        # Fallback template không chứa giá tiền
        hook = f"{hook_prefix} Ai mà ngờ món đồ này lại tiện đến thế!"
        body = f"Sản phẩm {title[:40]} đang làm mưa làm gió vì thiết kế cực kỳ thông minh, nhỏ gọn và tiện lợi, dùng một lần là mê ngay!"
        cta = "Mọi người bấm ngay vào link sản phẩm bên dưới góc trái để săn ưu đãi cực tốt hôm nay nhé!"
        full_text = f"{hook} {body} {cta}"
        caption = f"Món đồ siêu tiện lợi ai cũng nên có! 🔥"
        hashtags = "#ShopeeVideo #ReviewShopee #GiaTotMoiNgay #DealHot"

        return {
            "hook": hook,
            "body": body,
            "cta": cta,
            "full_voice_text": full_text,
            "caption": caption,
            "hashtags": hashtags
        }
