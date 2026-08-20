import asyncio
import edge_tts
from pathlib import Path

class TTSGenerator:
    def __init__(self):
        pass

    async def _generate_audio_async(self, text: str, voice: str, output_path: str, rate: str = "+6%"):
        """Tạo file voice MP3 từ text bằng Edge-TTS miễn phí"""
        communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
        await communicate.save(output_path)

    def generate_voice(self, text: str, voice: str, output_path: str, rate: str = "+6%") -> str:
        """Hàm đồng bộ bọc ngoài để gọi dễ dàng từ pipeline"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        asyncio.run(self._generate_audio_async(text, voice, output_path, rate))
        return output_path
