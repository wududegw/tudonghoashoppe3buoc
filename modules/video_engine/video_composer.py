import os
import random
from pathlib import Path
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeVideoClip, 
    TextClip, concatenate_videoclips, CompositeAudioClip
)
from config.settings import BGM_DIR

class VideoComposer:
    def __init__(self, output_size=(1080, 1920)):
        self.output_size = output_size

    def create_ken_burns_clip(self, img_path: str, duration: float, zoom_in: bool = True):
        """Tạo hiệu ứng phóng to/thu nhỏ nhẹ nhàng (Ken Burns) để ảnh không bị tĩnh"""
        clip = ImageClip(img_path).set_duration(duration)
        
        # Tỉ lệ scale mượt từ 1.0 đến 1.12
        def resize_func(t):
            if zoom_in:
                return 1.0 + 0.12 * (t / duration)
            else:
                return 1.12 - 0.12 * (t / duration)
                
        # Resize nhẹ và căn giữa
        zoomed_clip = clip.resize(resize_func).set_position(("center", "center"))
        return CompositeVideoClip([zoomed_clip], size=self.output_size).set_duration(duration)

    def render_video(self, clean_image_paths: list, voice_audio_path: str, 
                     title: str, price: str, output_mp4: str) -> str:
        """Ghép hoàn chỉnh video 9:16 chuẩn Shopee Video có chống quét trùng lặp"""
        Path(output_mp4).parent.mkdir(parents=True, exist_ok=True)

        voice_clip = AudioFileClip(voice_audio_path)
        total_duration = voice_clip.duration

        # 1. Phân bổ thời lượng các ảnh
        num_images = max(len(clean_image_paths), 1)
        duration_per_img = total_duration / num_images

        img_clips = []
        for idx, img_p in enumerate(clean_image_paths):
            zoom_direction = (idx % 2 == 0)
            c = self.create_ken_burns_clip(img_p, duration_per_img, zoom_in=zoom_direction)
            img_clips.append(c)

        main_video = concatenate_videoclips(img_clips, method="compose")

        # 2. Tạo các thẻ Text Overlay (Header, Giá Sale, Nút CTA)
        overlays = [main_video]

        try:
            # Banner Header
            header_badge = (
                TextClip("🔥 SIÊU SALE HÔM NAY", fontsize=55, color="yellow", bg_color="black", font="Arial-Bold")
                .set_position(("center", 180))
                .set_duration(total_duration)
            )
            overlays.append(header_badge)

            # Banner Giá
            price_text = f"CHỈ CÒN: {price}" if price else "SALE SỐC"
            price_badge = (
                TextClip(price_text, fontsize=65, color="white", bg_color="red", font="Arial-Bold")
                .set_position(("center", 280))
                .set_duration(total_duration)
            )
            overlays.append(price_badge)

            # Banner CTA Chỉ tay giỏ hàng
            cta_badge = (
                TextClip("👇 Bấm vào giỏ hàng góc trái săn ngay!", fontsize=42, color="white", bg_color="rgba(0,0,0,0.7)", font="Arial-Bold")
                .set_position(("center", 1680))
                .set_duration(total_duration)
            )
            overlays.append(cta_badge)
        except Exception as e:
            print(f"[VideoComposer] Bỏ qua TextClip nếu thiếu ImageMagick: {e}")

        final_composite = CompositeVideoClip(overlays, size=self.output_size).set_duration(total_duration)

        # 3. Lồng nhạc nền nhẹ (BGM) ngẫu nhiên nếu có
        bgm_files = list(BGM_DIR.glob("*.mp3"))
        if bgm_files:
            chosen_bgm = random.choice(bgm_files)
            bgm_clip = AudioFileClip(str(chosen_bgm)).subclip(0, total_duration).volumex(0.12)
            final_audio = CompositeAudioClip([voice_clip.volumex(1.0), bgm_clip])
        else:
            final_audio = voice_clip

        final_composite = final_composite.set_audio(final_audio)

        # 4. Render file MP4
        final_composite.write_videofile(
            output_mp4,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            logger=None
        )

        # Dọn dẹp clip
        voice_clip.close()
        final_composite.close()

        print(f"[VideoComposer] ✅ Đã xuất video thành công: {output_mp4}")
        return output_mp4
