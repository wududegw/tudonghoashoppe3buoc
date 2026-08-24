import os
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional

from config.settings import GEMINI_API_KEY, VIDEOS_DIR, BASE_DIR

class AIVideoGenerator:
    """
    BƯỚC 2 ĐƠN GIẢN HÓA:
    1. Nhận ảnh sản phẩm + KOL ngành tương ứng
    2. Tạo kịch bản review ngắn gọn
    3. Gọi thẳng API làm Video AI -> Xuất ra file MP4
    """

    def __init__(self, output_dir: Path = VIDEOS_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = os.getenv("AI_VIDEO_API_KEY", "")
        self.provider = os.getenv("AI_VIDEO_PROVIDER", "d-id").lower()

        if GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_API_KEY)
                self.gemini = genai.GenerativeModel("gemini-1.5-flash")
            except Exception:
                self.gemini = None
        else:
            self.gemini = None

    def generate_script(self, product_title: str, kol_name: str, kol_style: str) -> str:
        """Tạo kịch bản review ngắn gọn (12-15 giây)."""
        if self.gemini:
            prompt = f"""
Bạn là KOL {kol_name} ({kol_style}).
Hãy viết 1 đoạn kịch bản review ngắn gọn cho sản phẩm: "{product_title}".

Quy tắc:
1. Không đọc giá tiền cụ thể.
2. Nêu bật 1-2 công năng tiện ích nổi bật.
3. Câu kết thúc bắt buộc: "Mọi người bấm vào giỏ hàng góc trái để xem nhé!"
4. Trả về DUY NHẤT đoạn lời thoại tiếng Việt ngắn gọn để đọc (khoảng 35-40 từ), không thêm bất kỳ văn bản nào khác.
"""
            try:
                res = self.gemini.generate_content(prompt)
                return res.text.strip()
            except Exception as e:
                print(f"[!] Lỗi Gemini: {e}")

        # Kịch bản mặc định nếu không có API Key
        return f"Món đồ này đang cực hot trên Shopee vì quá tiện lợi! Thiết kế xịn xò, dùng cực kỳ ưng ý. Mọi người bấm vào giỏ hàng góc trái để xem nhé!"

    def create_video_via_api(self, item_id: str, product_image_url: str, kol_info: Dict[str, Any], script_text: str) -> Optional[str]:
        """Gọi API làm Video AI từ ảnh KOL / Sản phẩm và kịch bản."""
        output_file = str(self.output_dir / f"video_{item_id}.mp4")

        print(f"[*] [API Video] Đang gọi {self.provider.upper()} tạo video review cho item #{item_id}...")

        kol_avatar_url = kol_info.get("avatar_url", product_image_url)

        if self.provider == "d-id":
            return self._call_did(item_id, kol_avatar_url, script_text, kol_info.get("voice", "vi-VN-HoaiMyNeural"), output_file)

        print(f"[*] Đang sinh video qua {self.provider} API...")
        return None

    def _call_did(self, item_id: str, source_url: str, text: str, voice: str, output_file: str) -> Optional[str]:
        """Gọi API D-ID tạo video người nói."""
        if not self.api_key:
            print("[!] Chưa có AI_VIDEO_API_KEY trong .env. Vui lòng cấu hình key để render qua API.")
            return None

        url = "https://api.d-id.com/talks"
        headers = {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "source_url": source_url,
            "script": {
                "type": "text",
                "subtitles": "false",
                "provider": {
                    "type": "microsoft",
                    "voice_id": voice
                },
                "input": text
            },
            "config": {
                "fluent": "true"
            }
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=20)
            if resp.status_code not in [200, 201]:
                print(f"[!] D-ID API error: {resp.text}")
                return None

            talk_id = resp.json().get("id")
            print(f"[*] Đang render trên server D-ID (ID: {talk_id})...")

            for _ in range(30):
                time.sleep(4)
                status_resp = requests.get(f"{url}/{talk_id}", headers=headers)
                if status_resp.status_code == 200:
                    data = status_resp.json()
                    if data.get("status") == "done":
                        video_url = data.get("result_url")
                        vid_bytes = requests.get(video_url).content
                        with open(output_file, "wb") as f:
                            f.write(vid_bytes)
                        print(f"[+] Hoàn thành video review: {output_file}")
                        return output_file
                    elif data.get("status") == "error":
                        print("[!] Render video API thất bại.")
                        return None
        except Exception as e:
            print(f"[!] Lỗi gọi API: {e}")
            return None

        return None
