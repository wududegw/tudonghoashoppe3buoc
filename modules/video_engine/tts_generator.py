import asyncio
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional
import edge_tts
from loguru import logger

from config.settings import TEMP_DIR

class TTSGenerator:
    """Tạo giọng lồng tiếng tiếng Việt tự nhiên bằng Edge-TTS theo từng phong cách KOL."""

    def __init__(self, temp_dir: Path = TEMP_DIR):
        self.temp_dir = temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def clean_text_for_tts(self, text: str) -> str:
        """Làm sạch văn bản trước khi đọc (xóa icon, hashtag, ký tự đặc biệt)."""
        cleaned = re.sub(r"#\S+", "", text)  # Xóa hashtag
        cleaned = re.sub(r"[^\w\s.,!?;:–\-àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]", " ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    async def _generate_audio_async(self, text: str, output_path: str, voice: str = "vi-VN-HoaiMyNeural", rate: str = "+0%", pitch: str = "+0Hz"):
        communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
        await communicate.save(output_path)

    def generate_voice(self, item_id: str, text: str, kol_config: Dict[str, Any], custom_output_file: Optional[str] = None) -> str:
        """
        Sinh file âm thanh mp3 thuyết minh:
        - Tự động áp dụng giọng Nữ (vi-VN-HoaiMyNeural) hoặc Nam (vi-VN-NamMinhNeural)
        - Áp dụng tốc độ (rate) và độ trầm bổng (pitch) tương ứng của từng KOL
        """
        clean_text = self.clean_text_for_tts(text)
        if not clean_text:
            clean_text = "Sản phẩm chất lượng tuyệt vời. Mọi người bấm vào giỏ hàng góc trái màn hình để xem nhé!"

        voice = kol_config.get("voice", "vi-VN-HoaiMyNeural")
        rate = kol_config.get("rate", "+0%")
        pitch = kol_config.get("pitch", "+0Hz")

        output_file = custom_output_file or str(self.temp_dir / f"tts_{kol_config.get('kol_id', 'kol')}_{item_id}.mp3")

        try:
            # Chạy async trong loop hiện tại hoặc loop mới
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        pool.submit(asyncio.run, self._generate_audio_async(clean_text, output_file, voice=voice, rate=rate, pitch=pitch)).result()
                else:
                    loop.run_until_complete(self._generate_audio_async(clean_text, output_file, voice=voice, rate=rate, pitch=pitch))
            except RuntimeError:
                asyncio.run(self._generate_audio_async(clean_text, output_file, voice=voice, rate=rate, pitch=pitch))

            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                logger.info(f"🎙️ [TTS] Đã tạo giọng đọc thành công cho item #{item_id} ({voice})")
                return output_file
            else:
                logger.warning("⚠️ File âm thanh tạo ra bị rỗng.")
                return ""
        except Exception as e:
            logger.error(f"❌ [TTS] Lỗi sinh giọng đọc Edge-TTS: {e}")
            return ""
