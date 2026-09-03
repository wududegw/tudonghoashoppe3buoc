import os
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from loguru import logger

from database.db_manager import db
from modules.crawler.dispatcher import ProductDispatcher
from modules.crawler.affiliate_helper import ShopeeAffiliateHelper
from modules.video_engine.video_generator import AIVideoGenerator

app = FastAPI(title="Shopee Video Automation Receiver API", version="2.0")

dispatcher = ProductDispatcher()
affiliate_helper = ShopeeAffiliateHelper()
video_gen = AIVideoGenerator()

class ProductPayload(BaseModel):
    item_id: str
    shop_id: Optional[str] = "0"
    title: str
    price: float = 0.0
    price_before_discount: Optional[float] = 0.0
    product_url: str
    images: List[str]
    category: Optional[str] = ""

def process_and_render_pipeline(payload: ProductPayload, kol: dict):
    """Tiến trình chạy ngầm: Viết kịch bản -> Dựng Video -> Đưa vào hàng đợi sẵn sàng đăng."""
    try:
        logger.info(f"🚀 [Webhook Pipeline] Bắt đầu xử lý video cho {payload.title} (KOL: {kol.get('name')})...")

        # 1. Tạo kịch bản review ngắn gọn
        script_text = video_gen.generate_script(
            product_title=payload.title,
            kol_name=kol.get("name", "KOL"),
            kol_style=kol.get("style", "")
        )

        # 2. Sinh video review (ưu tiên Local Video Engine)
        first_image = payload.images[0] if payload.images else ""
        video_path = video_gen.create_video_via_api(
            item_id=payload.item_id,
            product_image_url=first_image,
            kol_info=kol,
            script_text=script_text
        )

        if video_path:
            # Lấy sản phẩm từ DB
            prod_row = db.get_connection().execute("SELECT id FROM products WHERE item_id = ?", (payload.item_id,)).fetchone()
            if prod_row:
                prod_id = prod_row["id"]
                queue_id = db.add_to_video_queue(
                    product_id=prod_id,
                    kol_id=kol.get("kol_id", "kol_01"),
                    script_hook="",
                    script_body=script_text,
                    caption=f"{payload.title[:45]}... Ghé ngay giỏ hàng góc trái săn deal nhé! 🔥",
                    hashtags="#ShopeeVideo #Review #DealHot"
                )
                db.update_video_queue(queue_id, video_path, status="ready_to_post")
                db.update_product_status(prod_id, "video_rendered", kol_id=kol.get("kol_id"))
                logger.success(f"🎬 Đã tạo video và nạp vào hàng đợi thành công: {video_path}")
    except Exception as e:
        logger.error(f"❌ Lỗi tiến trình tạo video webhook: {e}")

@app.post("/api/webhook/shopee-product")
def receive_shopee_product(payload: ProductPayload, background_tasks: BackgroundTasks):
    """
    Webhook tiếp nhận sản phẩm tự động:
    1. Kiểm tra chống trùng lặp trong Database
    2. Tự động gán KOL phụ trách theo ngành hàng
    3. Tự động sinh link Affiliate có gắn SubID của KOL
    4. Kích hoạt dựng video ngầm
    """
    if db.is_product_exists(payload.item_id, payload.shop_id):
        return {
            "status": "DUPLICATE_SKIPPED",
            "message": f"Sản phẩm {payload.item_id} đã tồn tại trong database. Bỏ qua để chống trùng!"
        }

    # Gán KOL
    kol = dispatcher.assign_kol(payload.dict())
    kol_id = kol.get("kol_id", "kol_01")
    device_id = kol.get("device_id", "emulator-5554")

    # Sinh link Affiliate
    affiliate_url = affiliate_helper.generate_affiliate_link(
        product_url=payload.product_url,
        kol_id=kol_id,
        device_id=device_id
    )

    product_dict = {
        "item_id": payload.item_id,
        "shop_id": payload.shop_id,
        "title": payload.title,
        "price": payload.price,
        "price_before_discount": payload.price_before_discount or payload.price,
        "product_url": payload.product_url,
        "affiliate_url": affiliate_url,
        "thumb_image": payload.images[0] if payload.images else "",
        "images": payload.images,
        "category": payload.category or kol.get("category", ""),
        "assigned_kol_id": kol_id
    }

    prod_id = db.insert_product(product_dict)
    if not prod_id:
        return {"status": "ERROR", "message": "Không thể lưu sản phẩm vào database"}

    # Tiến trình dựng video ngầm
    background_tasks.add_task(process_and_render_pipeline, payload, kol)

    return {
        "status": "SUCCESS",
        "message": f"Tiếp nhận sản phẩm thành công! Đã gán cho KOL {kol.get('name')} ({kol.get('category')})",
        "product_id": prod_id,
        "assigned_kol": kol.get("name"),
        "affiliate_url": affiliate_url
    }

@app.get("/api/stats")
def get_system_stats():
    """Báo cáo thống kê sản phẩm, hàng đợi và tình trạng các máy Box Phone."""
    total_products = db.get_products_count()
    device_stats = db.get_all_device_stats()
    return {
        "total_products": total_products,
        "active_devices": device_stats,
        "total_kols": 10
    }
