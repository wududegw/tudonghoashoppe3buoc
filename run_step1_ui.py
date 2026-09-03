import os
import sys
import json
import csv
import io
import webbrowser
import threading
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from loguru import logger

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from database.db_manager import DatabaseManager
from modules.crawler.shopee_crawler import ShopeeCrawler
from modules.crawler.dispatcher import ProductDispatcher
from modules.video_engine.video_generator import AIVideoGenerator
from config.settings import AI_VIDEO_PROVIDER, AI_VIDEO_API_KEY, VIDEO_ENGINE_MODE

HTML_TEMPLATE_PATH = BASE_DIR / "modules" / "crawler_ui" / "templates" / "index.html"
PORT = 8888

db_mgr = DatabaseManager()
crawler = ShopeeCrawler(db_mgr)
dispatcher = ProductDispatcher()
video_gen = AIVideoGenerator()

class CrawlerHTTPHandler(BaseHTTPRequestHandler):
    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            with open(HTML_TEMPLATE_PATH, "r", encoding="utf-8") as f:
                self.wfile.write(f.read().encode("utf-8"))

        elif path == "/api/products":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            products = db_mgr.get_all_products(limit=1000)
            resp = json.dumps({"products": products}, ensure_ascii=False)
            self.wfile.write(resp.encode("utf-8"))

        elif path == "/api/config":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            cfg = {
                "provider": video_gen.provider,
                "engine_mode": video_gen.engine_mode,
                "has_api_key": bool(video_gen.api_key)
            }
            self.wfile.write(json.dumps(cfg).encode("utf-8"))

        elif path == "/api/export-csv":
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8-sig")
            self.send_header("Content-Disposition", 'attachment; filename="shopee_products_affiliate.csv"')
            self.send_cors_headers()
            self.end_headers()

            products = db_mgr.get_all_products(limit=2000)
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "ID", "Tên Shop", "Tên sản phẩm", "Giá (đ)", "Lượt bán", "Đánh giá",
                "KOL Phụ trách", "Link Shopee Gốc", "Link Tiếp Thị (Affiliate SubID)", "Ngày Đăng"
            ])
            for p in products:
                writer.writerow([
                    p.get("item_id"),
                    p.get("shop_name", "Shop Official"),
                    p.get("title"),
                    p.get("price_formatted", p.get("price")),
                    p.get("historical_sold", 0),
                    p.get("rating_star", 5.0),
                    p.get("assigned_kol_id", ""),
                    p.get("product_url", ""),
                    p.get("affiliate_url", ""),
                    p.get("created_date", "")
                ])
            self.wfile.write(output.getvalue().encode("utf-8-sig"))

        else:
            self.send_response(404)
            self.send_cors_headers()
            self.end_headers()

    def do_POST(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        if path == "/api/open-shopee":
            try:
                data = json.loads(body) if body else {}
                url = data.get("url", "https://shopee.vn")
                chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
                if os.path.exists(chrome_path):
                    import subprocess
                    subprocess.Popen([chrome_path, url])
                else:
                    webbrowser.open(url)

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "opened_url": url}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

        elif path == "/api/crawl":
            try:
                data = json.loads(body)
                keywords = data.get("keywords", ["đồ gia dụng"])
                limit = data.get("limit", 20)
                min_sold = data.get("min_sold", 0)
                sort_by = data.get("sort_by", "sales")

                total_new = 0
                for kw in keywords:
                    kw_clean = kw.strip()
                    if not kw_clean:
                        continue

                    if "shopee.vn" in kw_clean or kw_clean.startswith("http"):
                        res = crawler.crawl_shop(shop_input=kw_clean, limit=limit, auto_save_db=True)
                        total_new += len(res)
                    else:
                        res = crawler.search_products(keyword=kw_clean, limit=limit, sort_by=sort_by, min_sold=min_sold, auto_save_db=True)
                        total_new += len(res)

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "crawled_count": total_new}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

        elif path == "/api/auto-video":
            """
            TIẾP NHẬN SẢN PHẨM TỪ EXTENSION & LÀM VIDEO NGAY LẬP TỨC:
            - Lưu sản phẩm vào DB (kèm Affiliate link SubID)
            - Tự động gọi Bước 2: Sinh kịch bản -> Gọi AI Video API -> Xuất MP4
            """
            try:
                data = json.loads(body)
                products = data.get("products", [])
                auto_render = data.get("auto_render", True)

                saved_count = 0
                rendered_videos = []

                for p in products:
                    kol = dispatcher.assign_kol(p)
                    p["assigned_kol_id"] = kol.get("kol_id", "kol_01")
                    if not p.get("affiliate_url"):
                        p["affiliate_url"] = crawler.affiliate_helper.generate_affiliate_link(
                            product_url=p.get("product_url", ""),
                            kol_id=p["assigned_kol_id"]
                        )
                    pid = db_mgr.insert_product(p)
                    p["id"] = pid if pid else (db_mgr.get_product_by_id(p.get("item_id")) or {}).get("id", 1)
                    saved_count += 1

                # BƯỚC 2: TỰ ĐỘNG GỌI API LÀM VIDEO CHO SẢN PHẨM MỚI (CHẠY THREAD KHÔNG NGHẼN MẠNG)
                if auto_render and products:
                    target = products[0]

                    def bg_video_worker(prod_data):
                        try:
                            kol = dispatcher.assign_kol(prod_data)
                            logger.info(f"🎬 [BƯỚC 2] Đang tự động gọi API làm video cho SP mới: '{prod_data.get('title')}' (KOL: {kol.get('name')})...")
                            script_data = video_gen.generate_full_script_data(prod_data, kol)
                            script_text = script_data.get("full_voice_text", "")

                            video_path = video_gen.create_video(
                                item_id=str(prod_data.get("item_id")),
                                image_urls=prod_data.get("images", [prod_data.get("thumb_image", "")]),
                                kol_info=kol,
                                script_text=script_text,
                                title=prod_data.get("title", "")
                            )

                            if video_path:
                                qid = db_mgr.add_to_video_queue(
                                    product_id=prod_data.get("id") or 1,
                                    kol_id=kol.get("kol_id", "kol_01"),
                                    script_hook=script_data.get("hook", ""),
                                    script_body=script_text,
                                    caption=script_data.get("caption", ""),
                                    hashtags=script_data.get("hashtags", "")
                                )
                                db_mgr.update_video_queue(qid, video_path, status="ready_to_post")
                                db_mgr.update_product_status(prod_data.get("id") or 1, "video_rendered", kol_id=kol.get("kol_id"))
                                logger.success(f"🎉 [BƯỚC 2 XONG] Video MP4 đã sẵn sàng: {video_path}")
                        except Exception as e_bg:
                            logger.error(f"❌ Lỗi tiến trình tạo video tự động: {e_bg}")

                    threading.Thread(target=bg_video_worker, args=(target,), daemon=True).start()

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "saved_count": saved_count,
                    "status": "making_video",
                    "target_product": products[0].get("title") if products else ""
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

        elif path == "/api/render-video":
            try:
                data = json.loads(body)
                product_id = data.get("product_id")
                prod = db_mgr.get_product_by_id(product_id)
                if not prod:
                    self.send_response(404)
                    self.send_cors_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Không tìm thấy sản phẩm"}).encode("utf-8"))
                    return

                kol = dispatcher.assign_kol(prod)
                script_data = video_gen.generate_full_script_data(prod, kol)
                script_text = script_data.get("full_voice_text", "")

                video_path = video_gen.create_video(
                    item_id=str(prod["item_id"]),
                    image_urls=prod.get("images", []),
                    kol_info=kol,
                    script_text=script_text,
                    title=prod.get("title", "")
                )

                if video_path:
                    queue_id = db_mgr.add_to_video_queue(
                        product_id=prod["id"],
                        kol_id=kol.get("kol_id", "kol_01"),
                        script_hook=script_data.get("hook", ""),
                        script_body=script_text,
                        caption=script_data.get("caption", ""),
                        hashtags=script_data.get("hashtags", "")
                    )
                    db_mgr.update_video_queue(queue_id, video_path, status="ready_to_post")
                    db_mgr.update_product_status(prod["id"], "video_rendered", kol_id=kol.get("kol_id"))

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": bool(video_path),
                    "video_path": video_path or "",
                    "kol": kol.get("name")
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

        elif path == "/api/clear":
            db_mgr.clear_all_products()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))

        else:
            self.send_response(404)
            self.send_cors_headers()
            self.end_headers()

    def log_message(self, format, *args):
        return

def open_browser():
    import time
    time.sleep(1.0)
    webbrowser.open(f"http://localhost:{PORT}")

def main():
    print("=" * 65)
    print(f"[*] SHOPEE PRODUCT CRAWLER & VIDEO AUTOMATION DASHBOARD")
    print(f"[*] Truy cập Dashboard tại: http://localhost:{PORT}")
    print("=" * 65)

    server = ThreadingHTTPServer(("0.0.0.0", PORT), CrawlerHTTPHandler)
    threading.Thread(target=open_browser, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng server.")
        server.server_close()

if __name__ == "__main__":
    main()
