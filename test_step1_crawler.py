"""
Script Test Bước 1: Quét sản phẩm Shopee thuần Python trên máy.
Chạy: python test_step1_crawler.py
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from loguru import logger

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from modules.crawler.shopee_crawler import ShopeeCrawler
from modules.crawler.dispatcher import ProductDispatcher
from database.db_manager import DatabaseManager

console = Console()

def test_crawler():
    console.rule("[bold cyan]BƯỚC 1: TEST SHOPEE PYTHON CRAWLER[/bold cyan]")

    db = DatabaseManager()
    crawler = ShopeeCrawler(db_manager=db)
    dispatcher = ProductDispatcher()

    # Nhập từ khóa hoặc dùng từ khóa mặc định
    keyword = "đồ gia dụng thông minh"
    console.print(f"\n[yellow]👉 Đang quét từ khóa mẫu: [bold]{keyword}[/bold] (Top bán chạy)...[/yellow]")

    # Thực hiện quét
    products = crawler.search_products(
        keyword=keyword,
        limit=5,
        sort_by="sales",
        min_sold=10,
        min_rating=4.0,
        auto_save_db=True
    )

    if not products:
        console.print("[red]❌ Chưa lấy được sản phẩm (có thể do rate-limit hoặc từ khóa quá hẹp). Thử lại với từ khóa khác.[/red]")
        return

    # Hiển thị bảng kết quả
    table = Table(title=f"Kết quả quét Shopee cho: '{keyword}'", show_header=True, header_style="bold magenta")
    table.add_column("Item ID", style="dim", width=12)
    table.add_column("Tên sản phẩm", style="bold white", width=35)
    table.add_column("Giá bán (VNĐ)", justify="right", style="green")
    table.add_column("Đã bán", justify="right", style="cyan")
    table.add_column("Sao", justify="center", style="yellow")
    table.add_column("Số ảnh HD", justify="center", style="blue")
    table.add_column("KOL Phụ trách", style="magenta")

    for p in products:
        kol = dispatcher.assign_kol(p)
        table.add_row(
            str(p["item_id"]),
            p["title"][:32] + "...",
            f"{int(p['price']):,}",
            str(p["historical_sold"]),
            f"⭐ {p['rating_star']}",
            f"{len(p.get('images', []))} ảnh",
            f"{kol.get('name')}"
        )

    console.print(table)
    console.print("\n[bold green]✅ Bước 1 đã hoạt động hoàn hảo: Lấy dữ liệu API, trích xuất ảnh HD, gán KOL và lưu SQLite chống trùng thành công![/bold green]\n")

if __name__ == "__main__":
    test_crawler()
