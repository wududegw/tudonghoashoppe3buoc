import os
import sys
import json
import csv
import io
import webbrowser
import threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from database.db_manager import DatabaseManager
from modules.crawler.shopee_crawler import ShopeeCrawler

HTML_TEMPLATE_PATH = BASE_DIR / "modules" / "crawler_ui" / "templates" / "index.html"
PORT = 8888

db_mgr = DatabaseManager()
crawler = ShopeeCrawler(db_mgr)

class CrawlerHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            with open(HTML_TEMPLATE_PATH, "r", encoding="utf-8") as f:
                self.wfile.write(f.read().encode("utf-8"))

        elif path == "/api/products":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            products = db_mgr.get_all_products(limit=1000)
            resp = json.dumps({"products": products}, ensure_ascii=False)
            self.wfile.write(resp.encode("utf-8"))

        elif path == "/api/export-csv":
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8-sig")
            self.send_header("Content-Disposition", 'attachment; filename="shopee_products.csv"')
            self.end_headers()

            products = db_mgr.get_all_products(limit=2000)
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["ID", "Tên Shop", "Tên sản phẩm", "Giá (đ)", "Lượt bán", "Đánh giá", "Ngày Đăng", "Ảnh Thumbnail", "Link Shopee"])
            for p in products:
                writer.writerow([
                    p.get("item_id"),
                    p.get("shop_name", "Shop Official"),
                    p.get("title"),
                    p.get("price_formatted", p.get("price")),
                    p.get("historical_sold", 0),
                    p.get("rating_star", 5.0),
                    p.get("created_date", ""),
                    p.get("thumb_image", ""),
                    p.get("product_url", "")
                ])
            self.wfile.write(output.getvalue().encode("utf-8-sig"))

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        if path == "/api/crawl":
            try:
                data = json.loads(body)
                keywords = data.get("keywords", ["đồ gia dụng"])
                limit = data.get("limit", 20)
                min_sold = data.get("min_sold", 0)
                sort_by = data.get("sort_by", "sales")

                total_new = 0
                for kw in keywords:
                    if kw.strip():
                        res = crawler.search_products(
                            keyword=kw.strip(),
                            limit=limit,
                            sort_by=sort_by,
                            min_sold=min_sold,
                            auto_save_db=True
                        )
                        total_new += len(res)

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "crawled_count": total_new}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

        elif path == "/api/clear":
            db_mgr.clear_all_products()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Tắt bớt log HTTP request thừa để console sạch
        return

def open_browser():
    """Tự động mở trình duyệt sau khi server khởi động."""
    import time
    time.sleep(1.0)
    webbrowser.open(f"http://localhost:{PORT}")

def main():
    print("=" * 60)
    print(f"[*] DANG KHOI CHAY SHOPEE PRODUCT CRAWLER DASHBOARD (BUOC 1)")
    print(f"[*] Truy cap Dashboard tai: http://localhost:{PORT}")
    print("=" * 60)

    server = HTTPServer(("0.0.0.0", PORT), CrawlerHTTPHandler)
    threading.Thread(target=open_browser, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDa dung server.")
        server.server_close()

if __name__ == "__main__":
    main()
