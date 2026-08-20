import shutil
import asyncio
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from database.db_manager import db
from modules.crawler_receiver.dispatcher import ChannelDispatcher
from modules.video_engine.image_cleaner import ImageCleaner
from modules.video_engine.script_generator import ScriptGenerator
from modules.video_engine.tts_generator import TTSGenerator
from modules.video_engine.video_composer import VideoComposer
from config.settings import OUTPUT_DIR

app = FastAPI(title="Shopee Video Matrix Automation API", version="2.0")

dispatcher = ChannelDispatcher()
cleaner = ImageCleaner()
script_gen = ScriptGenerator()
tts_gen = TTSGenerator()
composer = VideoComposer()

class ProductPayload(BaseModel):
    item_id: str
    shop_id: Optional[str] = "0"
    title: str
    price: str
    original_price: Optional[str] = ""
    url: str
    images: List[str]
    category: Optional[str] = ""

def process_and_render_pipeline(payload: ProductPayload, category_key: str, kol: dict):
    """Tiến trình chạy ngầm: Tải ảnh -> Làm sạch -> Viết kịch bản -> Lồng tiếng -> Render MP4 -> Nạp Queue"""
    work_dir = OUTPUT_DIR / f"temp_{payload.item_id}_{kol['channel_id']}"
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        print(f"[Pipeline] 🎨 1. Bóc tách & Làm sạch ảnh cho {payload.title}...")
        clean_images = cleaner.process_product_images(payload.images, work_dir)
        if not clean_images:
            raise Exception("Không tải hoặc làm sạch được ảnh sản phẩm nào")

        print(f"[Pipeline] ✍️ 2. Gemini sinh kịch bản theo Persona '{kol['kol_name']}'...")
        script_data = script_gen.generate_script(
            title=payload.title,
            price=payload.price,
            original_price=payload.original_price,
            kol_name=kol["kol_name"],
            tone=kol["tone"],
            category=category_key,
            default_hashtags=kol["hashtags_default"]
        )

        print(f"[Pipeline] 🎙️ 3. Edge-TTS tạo giọng đọc '{kol['tts_voice']}'...")
        voice_path = str(work_dir / "voiceover.mp3")
        tts_gen.generate_voice(script_data["voiceover_text"], kol["tts_voice"], voice_path)

        print(f"[Pipeline] 🎬 4. Ghép Video 9:16 có chuyển động & Anti-duplicate...")
        output_mp4 = str(OUTPUT_DIR / f"video_{kol['channel_id']}_{payload.item_id}.mp4")
        composer.render_video(
            clean_image_paths=clean_images,
            voice_audio_path=voice_path,
            title=payload.title,
            price=payload.price,
            output_mp4=output_mp4
        )

        # 5. Đẩy vào hàng đợi để Box Phone nhận việc
        caption_full = f"{script_data['caption']} {' '.join(script_data['hashtags'])}"
        db.add_to_queue(
            item_id=payload.item_id,
            kol_channel=category_key,
            device_id=kol["device_id"],
            product_url=payload.url,
            title=payload.title,
            price=payload.price,
            caption=caption_full,
            video_path=output_mp4
        )
        print(f"[Pipeline] 🚀 ĐÃ NẠP VIDEO VÀO HÀNG ĐỢI CHO MÁY {kol['device_id']} THÀNH CÔNG!")

    except Exception as e:
        print(f"[Pipeline] ❌ Lỗi xử lý video SP {payload.item_id}: {e}")
    finally:
        # Dọn dẹp thư mục ảnh tạm
        if work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)

@app.post("/api/webhook/shopee-product")
def receive_shopee_product(payload: ProductPayload, background_tasks: BackgroundTasks):
    """
    Webhook nhận dữ liệu sản phẩm từ Google Apps Script / Telegram Bot:
    1. Kiểm tra chống đăng trùng trên Database
    2. AI tự động điều hướng về 1 trong 10 kênh KOL phù hợp
    3. Kích hoạt Render Video tự động
    """
    # 1. AI Phân loại ngành hàng
    category_key = dispatcher.dispatch_category(payload.title, payload.category)
    kol = dispatcher.get_kol_profile(category_key)

    # 2. CHỐNG TRÙNG SẢN PHẨM TUYỆT ĐỐI
    if db.is_product_posted_on_channel(payload.item_id, category_key):
        return {
            "status": "SKIPPED",
            "message": f"Sản phẩm {payload.item_id} đã từng được đăng trên kênh {kol['channel_name']}. Bỏ qua để chống trùng!"
        }

    if db.is_product_in_queue(payload.item_id, category_key):
        return {
            "status": "QUEUED_ALREADY",
            "message": f"Sản phẩm {payload.item_id} đang nằm trong hàng đợi xử lý của kênh {kol['channel_name']}."
        }

    # Lưu vào database sản phẩm
    db.add_product(
        item_id=payload.item_id,
        shop_id=payload.shop_id,
        title=payload.title,
        price=payload.price,
        original_price=payload.original_price,
        url=payload.url,
        raw_images=payload.images,
        category=category_key
    )

    # Đưa vào tiến trình render ngầm
    background_tasks.add_task(process_and_render_pipeline, payload, category_key, kol)

    return {
        "status": "SUCCESS",
        "message": f"Đã tiếp nhận sản phẩm và chuyển giao cho KOL '{kol['kol_name']}' ({kol['channel_name']})",
        "assigned_kol": kol["kol_name"],
        "assigned_device": kol["device_id"]
    }

@app.get("/api/stats")
def get_system_stats():
    """Lấy báo cáo thống kê tình trạng 10 máy Box Phone và hàng đợi"""
    stats = db.get_all_device_stats()
    return {
        "devices": stats,
        "total_active_kols": 10
    }
