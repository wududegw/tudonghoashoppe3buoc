import asyncio
from pathlib import Path
import edge_tts
from loguru import logger

from config.settings import TEMP_DIR

class TTSGenerator:
    """Tạo giọng lồng tiếng tự nhiên bằng Edge-TTS theo từng KOL."""

    def __init__(self, temp_dir: Path = TEMP_DIR):
        self.temp_dir = temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def _generate_audio_async(self, text: str, output_path: str, voice: str = "vi-VN-HoaiMyNeural", rate: str = "+0%", pitch: str = "+0Hz"):
        communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
        await communicate.save(output_path)

    def generate_voice(self, item_id: str, text: str, kol_config: dict) -> str:
        """Sinh file mp3 âm thanh thuyết minh cho sản phẩm."""
        voice = kol_config.get("voice", "vi-VN-HoaiMyNeural")
        rate = kol_config.get("rate", "+0%")
        pitch = kol_config.get("pitch", "+0Hz")

        output_file = str(self.temp_dir / f"tts_{item_id}.mp3")

        try:
            asyncio.run(self._generate_audio_async(text, output_file, voice=voice, rate=rate, pitch=pitch))
            logger.info(f"🎙️ [TTS] Đã tạo giọng đọc cho item {item_id} ({voice})")
            return output_file
        except Exception as e:
            logger.error(f"❌ [TTS] Lỗi sinh giọng đọc: {e}")
            return ""
