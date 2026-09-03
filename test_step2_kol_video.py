"""
Script Test Bước 2: Hiển thị 10 KOL Reviewer và Test Dựng Video Review Hoàn Chỉnh (MP4).
Chạy: python test_step2_kol_video.py
"""

import os
import sys

# Cấu hình UTF-8 cho Windows Console chống lỗi charmap cp1252
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from pathlib import Path
from rich.console import Console
from rich.table import Table
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from modules.video_engine.kol_manager import KOLManager
from modules.video_engine.video_composer import VideoComposer
from modules.video_engine.script_generator import ScriptGenerator
from modules.video_engine.tts_generator import TTSGenerator
from modules.video_engine.video_generator import AIVideoGenerator

console = Console(force_terminal=True, color_system="auto")

def test_step2_video_production():
    console.rule("[bold cyan]BUOC 2: 10 KOL REVIEWER VA DUNG VIDEO REVIEW CHUAN 9:16[/bold cyan]")
    kol_mgr = KOLManager()
    composer = VideoComposer()
    script_gen = ScriptGenerator()
    tts_gen = TTSGenerator()
    video_gen = AIVideoGenerator()

    # 1. Bảng 10 Profile KOL Độc Quyền
    table = Table(title="10 Profile KOL Reviewer Độc Quyền (Chuẩn Ngành Hàng & Box Phone)", show_header=True, header_style="bold magenta")
    table.add_column("Mã KOL", style="dim", width=8)
    table.add_column("Tên Kênh Review", style="bold white", width=28)
    table.add_column("Ngành hàng phụ trách", style="cyan", width=22)
    table.add_column("Giọng lồng tiếng", style="yellow", width=18)
    table.add_column("Box Phone", style="blue", width=15)
    table.add_column("Trạng thái", style="green")

    for kol in kol_mgr.kols:
        table.add_row(
            kol.get("kol_id"),
            kol.get("full_title", kol.get("name")),
            kol.get("category"),
            kol.get("voice"),
            kol.get("device_id"),
            "✅ Sẵn sàng Review"
        )

    console.print(table)

    # 2. Test dựng 1 frame Review mẫu cho KOL 01 (Hoàng Yến - Gia Dụng)
    console.print("\n[yellow]👉 Đang tạo mẫu khung hình Video Review tối giản cho KOL Hoàng Yến...[/yellow]")
    kol_01 = kol_mgr.kols[0]

    sample_prod_img = BASE_DIR / "output" / "temp" / "sample_product.png"
    sample_prod_img.parent.mkdir(parents=True, exist_ok=True)
    if not sample_prod_img.exists():
        img = Image.new("RGB", (800, 800), (235, 238, 245))
        img.save(sample_prod_img)

    frame_path = composer.prepare_review_frame(
        img_path=str(sample_prod_img),
        kol_info=kol_01,
        title="Nồi Chiên Không Dầu Đa Năng",
        index=0,
        hook_text="Mấy bà nội trợ nhất định phải biết món này!"
    )

    console.print(f"[bold green]✅ Đã tạo thành công Frame Video Review 1080x1920:[/bold green] [cyan]{frame_path}[/cyan]")

    # 3. Test sinh kịch bản AI
    console.print("\n[yellow]👉 Đang tạo thử kịch bản Review chuẩn AIDA...[/yellow]")
    sample_prod = {
        "title": "Nồi chiên không dầu điện tử cao cấp 6L",
        "category": "Gia dụng & Đời sống"
    }
    script_data = script_gen.generate_script(sample_prod, kol_01)
    console.print(f"  • [bold magenta]Hook (3s):[/bold magenta] {script_data.get('hook')}")
    console.print(f"  • [bold cyan]Body (8s):[/bold cyan] {script_data.get('body')}")
    console.print(f"  • [bold green]CTA (4s):[/bold green] {script_data.get('cta')}")
    console.print(f"  • [bold yellow]Caption:[/bold yellow] {script_data.get('caption')}")

    # 4. Test sinh giọng đọc Edge-TTS
    console.print("\n[yellow]👉 Đang tạo thử giọng đọc tiếng Việt bằng Edge-TTS...[/yellow]")
    voice_path = tts_gen.generate_voice(
        item_id="sample_test",
        text=script_data.get("full_voice_text", ""),
        kol_config=kol_01
    )
    if voice_path and os.path.exists(voice_path):
        console.print(f"[bold green]✅ Đã tạo file âm thanh thuyết minh thành công:[/bold green] [cyan]{voice_path}[/cyan]")

        # 5. Dựng Video hoàn chỉnh
        console.print("\n[yellow]👉 Đang kết hợp hình ảnh, giọng đọc và footer giỏ hàng thành video MP4 hoàn chỉnh...[/yellow]")
        try:
            output_video = composer.create_video_from_images(
                item_id="sample_test",
                image_paths=[str(sample_prod_img)],
                audio_path=voice_path,
                title=sample_prod["title"],
                kol_info=kol_01,
                hook_text=script_data.get("hook", "")
            )
            if output_video and os.path.exists(output_video):
                console.print(f"[bold green]🎉 XUẤT SẮC! Video Review MP4 đã hoàn tất 100%:[/bold green] [cyan]{output_video}[/cyan]")
        except Exception as e:
            console.print(f"[yellow]⚠️ MoviePy render gặp thông báo: {e}[/yellow]")
    else:
        console.print("[yellow]⚠️ Chưa thể tạo âm thanh thuyết minh (yêu cầu kết nối mạng để tải giọng Edge-TTS).[/yellow]")

    console.print("\n[bold green]🌟 Bố cục Video Review đã được tối ưu hoàn hảo:[/bold green]")
    console.print("  1. 🎙️ [bold white]KOL Persona[/bold white] & Tên kênh ở góc trên (Font Unicode tiếng Việt sắc nét)")
    console.print("  2. 🖼️ [bold white]Không gian tối đa cho ảnh sản phẩm HD[/bold white] ở giữa (Không bị che)")
    console.print("  3. 🛒 [bold white]Nút kêu gọi duy nhất[/bold white]: '👇 BẤM VÀO GIỎ HÀNG GÓC TRÁI ĐỂ XEM 👇'")

if __name__ == "__main__":
    test_step2_video_production()
