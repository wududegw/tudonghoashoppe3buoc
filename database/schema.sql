CREATE TABLE IF NOT EXISTS products (
    item_id VARCHAR(50) PRIMARY KEY,
    shop_id VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    price VARCHAR(50),
    original_price VARCHAR(50),
    url TEXT NOT NULL,
    raw_images TEXT,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS posted_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id VARCHAR(50) NOT NULL,
    shop_id VARCHAR(50) NOT NULL,
    kol_channel VARCHAR(50) NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    video_path TEXT,
    caption TEXT,
    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(item_id, kol_channel)
);

CREATE TABLE IF NOT EXISTS video_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id VARCHAR(50) NOT NULL,
    kol_channel VARCHAR(50) NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    product_url TEXT NOT NULL,
    title TEXT NOT NULL,
    price VARCHAR(50),
    caption TEXT,
    video_path TEXT,
    status VARCHAR(20) DEFAULT 'PENDING',
    retry_count INTEGER DEFAULT 0,
    error_msg TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS device_stats (
    device_id VARCHAR(50) PRIMARY KEY,
    kol_channel VARCHAR(50) NOT NULL,
    today_date DATE NOT NULL,
    posted_count INTEGER DEFAULT 0,
    last_posted_at TIMESTAMP
);
