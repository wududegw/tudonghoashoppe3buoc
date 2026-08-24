"""
Shopee Video Automation - Quy Trình Khép Kín 3 Bước Tối Giản:
1. Bước 1: Quét sản phẩm Shopee thuần Python trên máy (ShopeeCrawler)
2. Bước 2: Lấy ảnh SP + KOL ngành tương ứng -> Gọi thẳng API sinh Video Review (AIVideoGenerator)
3. Bước 3: Tự động nạp vào Box Phone Farm đăng bài (SchedulerWorker)
"""

import sys
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

console = Console()

class ShopeeAutomationPipeline:
    def __init__(self):
        self.db = DatabaseManager()
        self.crawler = ShopeeCrawler(self.db)
        self.dispatcher = ProductDispatcher(KOLS_CONFIG_PATH)
        self.video_gen = AIVideoGenerator()
        self.notifier = TelegramNotifier()

    def run_step1_crawler(self):
        """Bước 1: Quét sản phẩm mới từ Shopee."""
        console.rule("[bold cyan]BƯỚC 1: QUÉT SẢN PHẨM SHOPEE (THUẦN PYTHON)[/bold cyan]")
        keywords = CRAWLER_CONFIG.get("default_keywords", [])
        logger.info(f"🔍 Quét {len(keywords)} nhóm từ khóa...")

        new_products = self.crawler.crawl_keywords_list(
            keywords=keywords,
            limit_per_keyword=CRAWLER_CONFIG.get("limit_per_keyword", 5)
        )
        logger.success(f"✅ Đã quét và lưu {len(new_products)} sản phẩm mới vào Database.")
        return new_products

    def run_step2_video_production(self):
        """Bước 2: Lấy ảnh SP + KOL tương ứng -> Gọi API làm Video Review."""
        console.rule("[bold magenta]BƯỚC 2: GỌI API LÀM VIDEO REVIEW VỚI KOL[/bold magenta]")
        pending_products = self.db.get_pending_products(limit=10)

        if not pending_products:
            logger.info("ℹ️ Không có sản phẩm nào cần làm video.")
            return

        for prod in pending_products:
            item_id = prod["item_id"]
            title = prod["title"]
            images = prod.get("images", [])
            first_image = images[0] if images else ""

            # 1. Lấy KOL tương ứng theo ngành hàng
            kol = self.dispatcher.assign_kol(prod)
            kol_id = kol.get("kol_id", "kol_01")
            kol_name = kol.get("name", "KOL")

            logger.info(f"🎙️ Gán #{item_id} cho KOL: {kol_name} ({kol.get('category')})")

            # 2. Tạo kịch bản review ngắn gọn
            script_text = self.video_gen.generate_script(
                product_title=title,
                kol_name=kol_name,
                kol_style=kol.get("style", "")
            )

            # 3. Gọi thẳng API làm Video AI
            video_path = self.video_gen.create_video_via_api(
                item_id=item_id,
                product_image_url=first_image,
                kol_info=kol,
                script_text=script_text
            )

            if video_path:
                queue_id = self.db.add_to_video_queue(
                    product_id=prod["id"],
                    kol_id=kol_id,
                    script_hook="",
                    script_body=script_text,
                    caption=f"{title[:40]}... Mọi người bấm vào giỏ hàng góc trái để xem nhé! #ShopeeVideo #Review",
                    hashtags="#ShopeeVideo #Review"
                )
                self.db.update_video_queue(queue_id, video_path, status="ready_to_post")
                self.db.update_product_status(prod["id"], "video_rendered", kol_id=kol_id)
                logger.success(f"🎬 Video review đã sẵn sàng: {video_path}")
            else:
                logger.warning(f"⚠️ Chưa tạo được video cho #{item_id} (Kiểm tra API Key)")

    def run_step3_box_phone_farm(self):
        """Bước 3: Vận hành Box Phone Farm đăng bài tự động."""
        console.rule("[bold green]BƯỚC 3: BOX PHONE FARM AUTO-POST[/bold green]")
        worker = SchedulerWorker(self.db, self.notifier)
        worker.run_worker_loop()

    def run_all(self):
        """Khởi chạy toàn bộ hệ thống."""
        console.print("[bold yellow]🚀 KHỞI ĐỘNG HỆ THỐNG SHOPEE AUTOMATION 3 BƯỚC[/bold yellow]\n")
        self.run_step1_crawler()
        self.run_step2_video_production()
        self.run_step3_box_phone_farm()

if __name__ == "__main__":
    pipeline = ShopeeAutomationPipeline()
    pipeline.run_all()
