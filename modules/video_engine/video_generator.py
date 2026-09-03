import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from loguru import logger

from config.settings import VIDEO_ENGINE_MODE, AI_VIDEO_PROVIDER, AI_VIDEO_API_KEY, VIDEOS_DIR, BASE_DIR
from modules.video_engine.script_generator import ScriptGenerator
from modules.video_engine.tts_generator import TTSGenerator
from modules.video_engine.image_cleaner import ImageCleaner
from modules.video_engine.video_composer import VideoComposer
from modules.video_engine.ai_video_api import AIVideoAPIClient

class AIVideoGenerator:
    """
    BỘ ĐIỀU PHỐI SẢN XUẤT VIDEO REVIEW BƯỚC 2:
    - Mặc định sử dụng Local Engine (MoviePy + Edge-TTS) miễn phí, tốc độ cao, chất lượng 1080p
    - Hỗ trợ Cloud API (D-ID) nếu người dùng cấu hình API Key
    - Tự động chuyển đổi kịch bản -> Lồng tiếng -> Ghép video hoàn chỉnh
    """

    def __init__(self, output_dir: Path = VIDEOS_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.engine_mode = VIDEO_ENGINE_MODE
        self.provider = AI_VIDEO_PROVIDER
        self.api_key = AI_VIDEO_API_KEY

        # Các module thành phần
        self.script_gen = ScriptGenerator()
        self.tts_gen = TTSGenerator()
        self.cleaner = ImageCleaner()
        self.composer = VideoComposer(output_dir=self.output_dir)
        self.api_client = AIVideoAPIClient(provider=self.provider, api_key=self.api_key, output_dir=self.output_dir)

    def generate_script(self, product_title: str, kol_name: str, kol_style: str, category: str = "") -> str:
        """Tạo kịch bản review ngắn gọn (12-15 giây) qua Gemini AI."""
        product_dummy = {"title": product_title, "category": category}
        kol_dummy = {"name": kol_name, "style": kol_style}
        data = self.script_gen.generate_script(product_dummy, kol_dummy)
        return data.get("full_voice_text", "")

    def generate_full_script_data(self, product: Dict[str, Any], kol_info: Dict[str, Any]) -> Dict[str, str]:
        """Tạo trọn bộ dữ liệu kịch bản: Hook, Body, CTA, Caption, Hashtags."""
        return self.script_gen.generate_script(product, kol_info)

    def create_video(
        self,
        item_id: str,
        image_urls: List[str],
        kol_info: Dict[str, Any],
        script_text: str,
        title: str = ""
    ) -> Optional[str]:
        """
        Dựng video review hoàn chỉnh:
        1. Ưu tiên Local Engine (MoviePy + Edge-TTS): Miễn phí, ổn định, đẹp mắt
        2. Nếu cấu hình engine_mode == "api": gọi Cloud D-ID API, fallback về Local nếu lỗi
        """
        kol_id = kol_info.get("kol_id", "kol_01")
        kol_name = kol_info.get("name", "KOL")
        logger.info(f"🎬 [Video Engine] Khởi chạy sản xuất video cho item #{item_id} (KOL: {kol_name}, Chế độ: {self.engine_mode.upper()})...")

        # 1. Tải và xử lý ảnh sản phẩm HD
        clean_images = self.cleaner.download_and_clean_images(item_id=item_id, image_urls=image_urls, max_images=4)
        if not clean_images:
            logger.error(f"❌ Không có ảnh sản phẩm hợp lệ cho item #{item_id}")
            return None

        # 2. Xử lý theo Cloud AI Video API nếu có API Key hoặc bật chế độ API
        if (self.engine_mode == "api" or self.api_key) and self.api_key.strip():
            logger.info(f"🌐 Đang tạo video qua AI Video API ({self.provider.upper()})...")
            avatar_path = kol_info.get("avatar_file", "")
            if avatar_path and not os.path.isabs(avatar_path):
                avatar_path = str(BASE_DIR / avatar_path)
            if not os.path.exists(avatar_path):
                avatar_path = kol_info.get("avatar_url", "")

            video_file = self.api_client.generate_kol_review_video(
                item_id=item_id,
                kol_avatar_path_or_url=avatar_path,
                script_text=script_text,
                voice_id=kol_info.get("voice", "vi-VN-HoaiMyNeural")
            )
            if video_file and os.path.exists(video_file):
                logger.success(f"🎉 Đã hoàn tất video AI qua API: {video_file}")
                return video_file
            logger.warning("⚠️ AI Video API gặp sự cố hoặc chưa có credit. Tự động chuyển tiếp sang Local Engine để luôn có video...")

        # 3. Dựng video bằng Local Engine (Edge-TTS + MoviePy)
        try:
            # Sinh giọng đọc tiếng Việt theo phong cách của KOL
            voice_file = self.tts_gen.generate_voice(item_id=item_id, text=script_text, kol_config=kol_info)
            if not voice_file or not os.path.exists(voice_file):
                logger.error("❌ Không sinh được file âm thanh thuyết minh.")
                return None

            # Render video 9:16 chuẩn nét
            output_mp4 = self.composer.create_video_from_images(
                item_id=item_id,
                image_paths=clean_images,
                audio_path=voice_file,
                title=title,
                kol_info=kol_info,
                hook_text=kol_info.get("hook_prefix", "")
            )

            return output_mp4 if output_mp4 and os.path.exists(output_mp4) else None

        except Exception as e:
            logger.error(f"❌ Lỗi quy trình dựng video cục bộ: {e}")
            return None

    def create_video_via_api(self, item_id: str, product_image_url: str, kol_info: Dict[str, Any], script_text: str) -> Optional[str]:
        """Tương thích ngược cho các lời gọi cũ."""
        image_urls = [product_image_url] if product_image_url else []
        return self.create_video(
            item_id=item_id,
            image_urls=image_urls,
            kol_info=kol_info,
            script_text=script_text
        )
