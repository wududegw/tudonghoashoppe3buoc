-- Bảng lưu trữ sản phẩm đã quét được (Chống trùng sản phẩm)
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL,
    shop_id TEXT NOT NULL,
    shop_name TEXT DEFAULT '',
    title TEXT NOT NULL,
    price REAL DEFAULT 0,
    price_before_discount REAL DEFAULT 0,
    discount_percent INTEGER DEFAULT 0,
    historical_sold INTEGER DEFAULT 0,
    rating_star REAL DEFAULT 0,
    product_url TEXT NOT NULL,
    affiliate_url TEXT,
    thumb_image TEXT DEFAULT '',
    images_json TEXT NOT NULL,
    category TEXT,
    assigned_kol_id TEXT,
    created_date TEXT,
    status TEXT DEFAULT 'pending',
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(item_id, shop_id)
);

-- Bảng hàng đợi render và đăng video
CREATE TABLE IF NOT EXISTS video_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    kol_id TEXT NOT NULL,
    video_path TEXT,
    script_hook TEXT,
    script_body TEXT,
    caption TEXT,
    hashtags TEXT,
    status TEXT DEFAULT 'queued',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(product_id) REFERENCES products(id)
);

-- Bảng lịch sử đăng bài của từng thiết bị Box Phone
CREATE TABLE IF NOT EXISTS posted_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    kol_id TEXT NOT NULL,
    device_id TEXT NOT NULL,
    video_path TEXT,
    caption TEXT,
    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'success',
    FOREIGN KEY(product_id) REFERENCES products(id)
);

-- Bảng thống kê thiết bị theo ngày
CREATE TABLE IF NOT EXISTS device_daily_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    stat_date DATE NOT NULL,
    post_count INTEGER DEFAULT 0,
    last_posted_at TIMESTAMP,
    UNIQUE(device_id, stat_date)
);
