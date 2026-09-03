"""
Shopee Video Automation - Quy Trình Khép Kín Tự Động Hóa:
1. Bước 1: Quét sản phẩm Shopee thuần Python trên máy (ShopeeCrawler) + Tự động sinh link Affiliate
2. Bước 2: Phân tích ngành hàng -> Gán KOL -> Gemini sinh kịch bản -> Lồng tiếng Edge-TTS -> Render Video 9:16 (AIVideoGenerator)
3. Bước 3: Đưa vào hàng đợi sẵn sàng cho Box Phone Farm (SchedulerWorker)
"""

import sys

# Cấu hình UTF-8 cho Windows Console chống lỗi charmap cp1252
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from pathlib import Path
from loguru import logger
from rich.console import Console

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import CRAWLER_CONFIG, KOLS_CONFIG_PATH
from database.db_manager import DatabaseManager
from modules.crawler.shopee_crawler import ShopeeCrawler
from modules.crawler.dispatcher import ProductDispatcher
from modules.video_engine.video_generator import AIVideoGenerator
from modules.box_phone_farm.scheduler_worker import SchedulerWorker
from utils.notifier import TelegramNotifier

console = Console(force_terminal=True, color_system="auto")

class ShopeeAutomationPipeline:
    def __init__(self):
        self.db = DatabaseManager()
        self.crawler = ShopeeCrawler(self.db)
        self.dispatcher = ProductDispatcher(KOLS_CONFIG_PATH)
        self.video_gen = AIVideoGenerator()
        self.notifier = TelegramNotifier()

    def run_step1_crawler(self, max_products: int = 10):
        """Bước 1: Quét sản phẩm mới từ Shopee và tự động sinh link tiếp thị liên kết (Affiliate Link)."""
        console.rule("[bold cyan]BƯỚC 1: QUÉT SẢN PHẨM SHOPEE & TẠO LINK AFFILIATE[/bold cyan]")
        keywords = CRAWLER_CONFIG.get("default_keywords", [])
        logger.info(f"🔍 Bắt đầu quét {len(keywords)} nhóm từ khóa mục tiêu...")

        new_products = self.crawler.crawl_keywords_list(
            keywords=keywords,
            limit_per_keyword=CRAWLER_CONFIG.get("limit_per_keyword", 3)
        )
        logger.success(f"✅ Đã quét, tạo link affiliate và lưu {len(new_products)} sản phẩm mới vào Database.")
        return new_products

    def run_step2_video_production(self, limit: int = 5):
        """Bước 2: Gán KOL -> Viết kịch bản AI -> Lồng tiếng chuẩn ngữ điệu -> Dựng Video Review 9:16."""
        console.rule("[bold magenta]BƯỚC 2: SẢN XUẤT VIDEO REVIEW VỚI KOL[/bold magenta]")
        pending_products = self.db.get_pending_products(limit=limit)

        if not pending_products:
            logger.info("ℹ️ Không có sản phẩm nào đang chờ dựng video.")
            return

        logger.info(f"🎬 Bắt đầu sản xuất video cho {len(pending_products)} sản phẩm trong hàng đợi...")

        for prod in pending_products:
            item_id = prod["item_id"]
            title = prod["title"]
            images = prod.get("images", [])

            # 1. Gán KOL tương ứng theo ngành hàng
            kol = self.dispatcher.assign_kol(prod)
            kol_id = kol.get("kol_id", "kol_01")
            kol_name = kol.get("name", "KOL")

            logger.info(f"🎙️ Gán #{item_id} ('{title[:30]}...') cho KOL: {kol_name} ({kol.get('category')})")

            # 2. Tạo kịch bản review chuẩn AIDA qua Gemini AI (không đọc giá cứng, lọc từ cấm)
            script_data = self.video_gen.generate_full_script_data(prod, kol)
            script_text = script_data.get("full_voice_text", "")

            # 3. Dựng Video 9:16 hoàn chỉnh (MoviePy + Edge-TTS + Ken-Burns + BGM)
            video_path = self.video_gen.create_video(
                item_id=item_id,
                image_urls=images,
                kol_info=kol,
                script_text=script_text,
                title=title
            )

            if video_path:
                queue_id = self.db.add_to_video_queue(
                    product_id=prod["id"],
                    kol_id=kol_id,
                    script_hook=script_data.get("hook", ""),
                    script_body=script_text,
                    caption=script_data.get("caption", f"{title[:40]}... Ghé ngay giỏ hàng góc trái săn deal nhé! 🔥"),
                    hashtags=script_data.get("hashtags", "#ShopeeVideo #Review #DealHot")
                )
                self.db.update_video_queue(queue_id, video_path, status="ready_to_post")
                self.db.update_product_status(prod["id"], "video_rendered", kol_id=kol_id)
                logger.success(f"🎬 Video review đã dựng xong và sẵn sàng: {video_path}")
            else:
                logger.warning(f"⚠️ Chưa tạo được video cho #{item_id}. Đã giữ lại trong hàng đợi.")

    def run_step3_box_phone_farm(self):
        """Bước 3: Vận hành Box Phone Farm đăng bài tự động (Đang chờ lệnh chạy)."""
        console.rule("[bold green]BƯỚC 3: BOX PHONE FARM AUTO-POST[/bold green]")
        worker = SchedulerWorker(self.db, self.notifier)
        worker.run_worker_loop()

    def run_step1_and_step2(self):
        """Khởi chạy toàn bộ Bước 1 và Bước 2."""
        console.print("[bold yellow]🚀 KHỞI ĐỘNG HỆ THỐNG SHOPEE AUTOMATION: BƯỚC 1 & BƯỚC 2[/bold yellow]\n")
        self.run_step1_crawler()
        self.run_step2_video_production()
        console.print("\n[bold green]🎉 Hoàn tất sản xuất video! Toàn bộ video đã được đưa vào hàng đợi SQLite sẵn sàng đăng.[/bold green]\n")

if __name__ == "__main__":
    pipeline = ShopeeAutomationPipeline()
    pipeline.run_step1_and_step2()
