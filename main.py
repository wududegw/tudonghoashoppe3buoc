import json
import uvicorn
from pathlib import Path
from config.settings import SERVER_HOST, SERVER_PORT, BASE_DIR
from database.db_manager import db
from modules.box_phone_farm.scheduler_worker import DeviceWorkerThread
from modules.crawler_receiver.api_server import app

def start_box_phone_workers():
    """Khởi động 10 tiến trình worker chạy ngầm cho 10 máy Box Phone"""
    config_file = BASE_DIR / "config" / "kols_config.json"
    with open(config_file, "r", encoding="utf-8") as f:
        kols_config = json.load(f)

    workers = []
    for category_key, kol_info in kols_config.items():
        worker = DeviceWorkerThread(
            device_id=kol_info["device_id"],
            kol_channel=category_key,
            kol_name=kol_info["kol_name"],
            daily_limit=kol_info.get("daily_limit", 50)
        )
        worker.start()
        workers.append(worker)

    print(f"🚀 Đã kích hoạt {len(workers)} luồng điều khiển Box Phone cho 10 KOL AI thành công!")
    return workers

if __name__ == "__main__":
    print("=" * 65)
    print("🔥 SHOPEE VIDEO MATRIX & BOX PHONE FARM AUTOMATION SYSTEM 🔥")
    print("=" * 65)

    # 1. Khởi tạo database
    db.init_db()
    print("✅ Database SQLite đã sẵn sàng.")

    # 2. Khởi động 10 Worker Box Phone
    workers = start_box_phone_workers()

    # 3. Chạy FastAPI Webhook Server để đón dữ liệu từ Google Script
    print(f"📡 Webhook API Server đang lắng nghe tại: http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"👉 Endpoint nhận sản phẩm mới: http://{SERVER_HOST}:{SERVER_PORT}/api/webhook/shopee-product")
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
