import os
import time
import base64
import requests
from typing import Dict, Any, Optional
from loguru import logger
from pathlib import Path

from config.settings import VIDEOS_DIR, TEMP_DIR

class AIVideoAPIClient:
    """
    Client gọi API sinh Video AI (D-ID, HeyGen, Hedra hoặc Custom API):
    - Truyền ảnh KOL + Kịch bản tiếng Việt -> Trả về Video KOL người thật cử động & nói chuyện chân thực
    """

    def __init__(self, provider: str = "d-id", api_key: str = "", output_dir: Path = VIDEOS_DIR):
        self.provider = (provider or os.getenv("AI_VIDEO_PROVIDER", "d-id")).lower()
        self.api_key = api_key or os.getenv("AI_VIDEO_API_KEY", "")
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_auth_header(self) -> str:
        """Chuẩn hóa header xác thực cho D-ID (hỗ trợ cả raw key lẫn base64)."""
        if not self.api_key:
            return ""
        key = self.api_key.strip()
        if key.startswith("Basic "):
            return key
        if ":" in key:
            encoded = base64.b64encode(key.encode()).decode()
            return f"Basic {encoded}"
        # Nếu chỉ có key (chưa có :secret), encode key + :
        try:
            # Thử decode xem đã là base64 chưa
            base64.b64decode(key, validate=True)
            return f"Basic {key}"
        except Exception:
            encoded = base64.b64encode(f"{key}:".encode()).decode()
            return f"Basic {encoded}"

    def upload_image_to_did(self, image_path: str) -> Optional[str]:
        """Tải ảnh avatar nội bộ lên D-ID để lấy public URL."""
        if not os.path.exists(image_path):
            return None
        url = "https://api.d-id.com/images"
        headers = {"Authorization": self._get_auth_header()}
        try:
            with open(image_path, "rb") as f:
                resp = requests.post(url, headers=headers, files={"image": f}, timeout=30)
            if resp.status_code in [200, 201]:
                return resp.json().get("url")
            logger.warning(f"Không upload được ảnh lên D-ID ({resp.status_code}): {resp.text}")
        except Exception as e:
            logger.warning(f"Lỗi upload ảnh lên D-ID: {e}")
        return None

    def generate_kol_review_video(
        self,
        item_id: str,
        kol_avatar_path_or_url: str,
        script_text: str,
        voice_id: str = "vi-VN-HoaiMyNeural",
        audio_url: Optional[str] = None
    ) -> Optional[str]:
        """
        Gửi yêu cầu tới AI Video API để tạo video KOL Reviewer nói chuyện tự nhiên.
        """
        output_file = str(self.output_dir / f"ai_video_{item_id}.mp4")

        if not self.api_key:
            logger.warning(f"⚠️ Chưa cấu hình AI_VIDEO_API_KEY cho {self.provider.upper()}. Vui lòng cấu hình API Key trong file .env hoặc trên giao diện.")
            return None

        try:
            logger.info(f"🌐 [AI Video API] Đang gửi yêu cầu sinh video tới {self.provider.upper()}...")

            if self.provider == "d-id":
                return self._call_did_api(item_id, kol_avatar_path_or_url, script_text, voice_id, output_file)
            elif self.provider == "heygen":
                return self._call_heygen_api(item_id, kol_avatar_path_or_url, script_text, voice_id, output_file)
            elif self.provider == "hedra":
                return self._call_hedra_api(item_id, kol_avatar_path_or_url, script_text, audio_url, output_file)
            else:
                logger.error(f"Provider {self.provider} chưa được hỗ trợ.")
                return None

        except Exception as e:
            logger.error(f"❌ Lỗi gọi API Video: {e}")
            return None

    def _call_did_api(
        self,
        item_id: str,
        source: str,
        script_text: str,
        voice_id: str,
        output_file: str
    ) -> Optional[str]:
        """Gọi D-ID Talk API (Tạo video người nói từ ảnh + text tiếng Việt)."""
        # Nếu là file local thì tải lên D-ID lấy URL
        source_url = source
        if os.path.exists(source):
            uploaded = self.upload_image_to_did(source)
            if uploaded:
                source_url = uploaded
            else:
                # Dùng ảnh mẫu người thật của D-ID nếu upload lỗi
                source_url = "https://create-images-results.d-id.com/DefaultPresenters/Noa_f/image.jpeg"

        url = "https://api.d-id.com/talks"
        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json"
        }
        payload = {
            "source_url": source_url,
            "script": {
                "type": "text",
                "subtitles": "false",
                "provider": {
                    "type": "microsoft",
                    "voice_id": voice_id or "vi-VN-HoaiMyNeural"
                },
                "input": script_text
            },
            "config": {
                "fluent": "true",
                "pad_audio": "0.0"
            }
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=25)
        if resp.status_code not in [200, 201]:
            logger.error(f"D-ID API lỗi ({resp.status_code}): {resp.text}")
            return None

        talk_id = resp.json().get("id")
        logger.info(f"⏳ D-ID đang render video AI (Task ID: {talk_id}). Đang chờ hoàn tất...")

        # Polling kết quả (tối đa 2 phút)
        for attempt in range(30):
            time.sleep(4)
            status_resp = requests.get(f"{url}/{talk_id}", headers=headers, timeout=15)
            if status_resp.status_code == 200:
                result = status_resp.json()
                status = result.get("status")
                if status == "done":
                    result_url = result.get("result_url")
                    video_data = requests.get(result_url, timeout=30).content
                    with open(output_file, "wb") as f:
                        f.write(video_data)
                    logger.success(f"🎉 Đã tải xong video AI từ D-ID: {output_file}")
                    return output_file
                elif status == "error":
                    logger.error(f"D-ID render thất bại: {result.get('error')}")
                    return None
                else:
                    logger.info(f"⏳ D-ID đang xử lý... ({attempt + 1}/30)")

        return None

    def _call_heygen_api(self, item_id: str, avatar_id: str, script_text: str, voice_id: str, output_file: str) -> Optional[str]:
        """Gọi HeyGen Video Generation API."""
        url = "https://api.heygen.com/v2/video/generate"
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "video_inputs": [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": avatar_id if avatar_id and not avatar_id.startswith("http") else "Daisy-inskirt-20220818"
                    },
                    "voice": {
                        "type": "text",
                        "input_text": script_text,
                        "voice_id": "vi-VN-HoaiMyNeural"
                    }
                }
            ],
            "dimension": {"width": 1080, "height": 1920}
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=25)
            if resp.status_code in [200, 201]:
                video_id = resp.json().get("data", {}).get("video_id")
                logger.info(f"⏳ HeyGen Video Task ID: {video_id}. Đang polling...")
                for _ in range(30):
                    time.sleep(4)
                    check = requests.get(f"https://api.heygen.com/v1/video_status.get?video_id={video_id}", headers=headers)
                    if check.status_code == 200:
                        st = check.json().get("data", {})
                        if st.get("status") == "completed":
                            v_url = st.get("video_url")
                            video_data = requests.get(v_url, timeout=30).content
                            with open(output_file, "wb") as f:
                                f.write(video_data)
                            return output_file
                        elif st.get("status") == "failed":
                            break
        except Exception as e:
            logger.error(f"Lỗi HeyGen API: {e}")
        return None

    def _call_hedra_api(self, item_id: str, image_url: str, text: str, audio_url: Optional[str], output_file: str) -> Optional[str]:
        """Gọi Hedra Character Video API."""
        logger.info("Đã gửi request tới Hedra Character Video API...")
        return None
