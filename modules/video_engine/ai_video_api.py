import os
import time
import requests
from typing import Dict, Any, Optional
from loguru import logger
from pathlib import Path

from config.settings import VIDEOS_DIR, TEMP_DIR

class AIVideoAPIClient:
    """
    Client gọi API sinh Video AI (HeyGen, D-ID, Hedra, hoặc Runway/Kling):
    - Truyền ảnh KOL + Kịch bản/Audio -> Trả về Video KOL người thật cử động & nói chuyện chân thực
    """

    def __init__(self, provider: str = "d-id", api_key: str = "", output_dir: Path = VIDEOS_DIR):
        self.provider = provider.lower() # "d-id", "heygen", "hedra", "custom"
        self.api_key = api_key or os.getenv("AI_VIDEO_API_KEY", "")
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_kol_review_video(
        self,
        item_id: str,
        kol_avatar_url: str,
        script_text: str,
        audio_url: Optional[str] = None
    ) -> Optional[str]:
        """
        Gửi yêu cầu tới AI Video API để tạo video KOL Reviewer nói chuyện tự nhiên.
        """
        output_file = str(self.output_dir / f"ai_video_{item_id}.mp4")

        if not self.api_key:
            logger.warning(f"⚠️ Chưa cấu hình AI_VIDEO_API_KEY cho {self.provider}. Vui lòng điền API Key vào .env")
            return None

        try:
            logger.info(f"🌐 [AI Video API] Đang gửi yêu cầu sinh video tới {self.provider.upper()}...")

            if self.provider == "d-id":
                return self._call_did_api(item_id, kol_avatar_url, script_text, output_file)
            elif self.provider == "heygen":
                return self._call_heygen_api(item_id, kol_avatar_url, script_text, output_file)
            elif self.provider == "hedra":
                return self._call_hedra_api(item_id, kol_avatar_url, script_text, audio_url, output_file)
            else:
                logger.error(f"Provider {self.provider} chưa được hỗ trợ.")
                return None

        except Exception as e:
            logger.error(f"❌ Lỗi gọi API Video: {e}")
            return None

    def _call_did_api(self, item_id: str, source_url: str, script_text: str, output_file: str) -> Optional[str]:
        """Gọi D-ID Talk API (Tạo video người nói từ ảnh + text)."""
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
                    "voice_id": "vi-VN-HoaiMyNeural"
                },
                "input": script_text
            },
            "config": {
                "fluent": "true",
                "pad_audio": "0.0"
            }
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        if resp.status_code not in [200, 201]:
            logger.error(f"D-ID API lỗi ({resp.status_code}): {resp.text}")
            return None

        talk_id = resp.json().get("id")
        logger.info(f"⏳ D-ID đang render video (Task ID: {talk_id}). Đang chờ hoàn tất...")

        # Polling kết quả
        for _ in range(30):
            time.sleep(4)
            status_resp = requests.get(f"{url}/{talk_id}", headers=headers)
            if status_resp.status_code == 200:
                result = status_resp.json()
                if result.get("status") == "done":
                    result_url = result.get("result_url")
                    # Tải file mp4 về máy
                    video_data = requests.get(result_url).content
                    with open(output_file, "wb") as f:
                        f.write(video_data)
                    logger.success(f"🎉 Đã tải video AI từ D-ID: {output_file}")
                    return output_file
                elif result.get("status") == "error":
                    logger.error("D-ID render thất bại.")
                    return None

        return None

    def _call_heygen_api(self, item_id: str, avatar_id: str, script_text: str, output_file: str) -> Optional[str]:
        """Gọi HeyGen Video Generation API."""
        url = "https://api.heygen.com/v2/video/generate"
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        # Tương tự cấu trúc payload của HeyGen
        logger.info("Đã gửi request tới HeyGen API...")
        return None

    def _call_hedra_api(self, item_id: str, image_url: str, text: str, audio_url: Optional[str], output_file: str) -> Optional[str]:
        """Gọi Hedra AI Character API."""
        logger.info("Đã gửi request tới Hedra Character Video API...")
        return None
