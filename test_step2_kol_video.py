"""
Script Test Bước 2: Hiển thị 10 KOL Reviewer và Test Dựng Frame Video Review cho KOL (Tối giản & Rộng rãi).
Chạy: python test_step2_kol_video.py
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from modules.video_engine.kol_manager import KOLManager
from modules.video_engine.video_composer import VideoComposer

console = Console()

def test_kol_and_review_layout():
    console.rule("[bold cyan]BƯỚC 2: 10 KOL REVIEWER & BỐ CỤC VIDEO REVIEW TỐI GIẢN[/bold cyan]")
    kol_mgr = KOLManager()
    composer = VideoComposer()

    table = Table(title="10 Profile KOL Reviewer Độc Quyền", show_header=True, header_style="bold magenta")
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

    # Test dựng 1 frame Review mẫu cho KOL 01 (Hoàng Yến - Gia Dụng)
    console.print("\n[yellow]👉 Đang tạo mẫu khung hình Video Review tối giản cho KOL Hoàng Yến...[/yellow]")
    kol_01 = kol_mgr.kols[0]

    sample_prod_img = BASE_DIR / "output" / "temp" / "sample_product.png"
    sample_prod_img.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (600, 600), (240, 240, 245))
    img.save(sample_prod_img)

    frame_path = composer.prepare_review_frame(
        img_path=str(sample_prod_img),
        kol_info=kol_01,
        title="Nồi Chiên Không Dầu",
        index=0
    )

    console.print(f"[bold green]✅ Đã tạo thành công Frame Video Review chuẩn 9:16:[/bold green] [cyan]{frame_path}[/cyan]")
    console.print("[bold green]🌟 Bố cục Video Review tối giản:[/bold green]")
    console.print("  1. 🎙️ [bold white]KOL Reviewer Avatar[/bold white] & Tên kênh ở góc trên")
    console.print("  2. 🖼️ [bold white]Không gian tối đa cho ảnh sản phẩm HD[/bold white] ở giữa (Không bị che)")
    console.print("  3. 🛒 [bold white]Nút kêu gọi duy nhất[/bold white]: '👇 BẤM VÀO GIỎ HÀNG GÓC TRÁI ĐỂ XEM 👇'")

if __name__ == "__main__":
    test_kol_and_review_layout()
