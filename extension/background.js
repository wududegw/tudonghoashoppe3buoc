/**
 * background.js - Service Worker: Theo dõi Shop Shopee ngầm & Tự động gọi API làm Video khi có SP mới
 */

const API_BACKEND_URL = "http://localhost:8888/api/auto-video";

// Khởi tạo trạng thái mặc định
chrome.runtime.onInstalled.addListener(() => {
    console.log("[Shopee Watcher] Extension đã sẵn sàng!");

    chrome.storage.local.get(["watched_shops", "known_item_ids", "auto_video_enabled", "scanned_products"], (res) => {
        const defaults = {};
        if (!res.watched_shops) {
            defaults.watched_shops = [
                { username: "balabala_official", name: "Balabala Official Store", shop_id: "87261521" },
                { username: "vanikids", name: "Vanikids VN", shop_id: "92154812" }
            ];
        }
        if (!res.known_item_ids) defaults.known_item_ids = ["229871101", "229871102", "229871103"];
        if (res.auto_video_enabled === undefined) defaults.auto_video_enabled = true;
        if (!res.scanned_products) defaults.scanned_products = [];

        chrome.storage.local.set(defaults);
    });

    // Tạo alarm kiểm tra shop định kỳ mỗi 2 phút
    chrome.alarms.create("watch_shopee_shops", { periodInMinutes: 2 });
});

// Lắng nghe alarm định kỳ
chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === "watch_shopee_shops") {
        checkWatchedShopsForNewItems();
    }
});

// Hàm kiểm tra các shop được theo dõi
async function checkWatchedShopsForNewItems() {
    chrome.storage.local.get(["watched_shops", "known_item_ids", "auto_video_enabled"], async (data) => {
        const watchedShops = data.watched_shops || [];
        const knownIds = new Set(data.known_item_ids || []);
        const autoVideo = data.auto_video_enabled !== false;

        if (watchedShops.length === 0) return;

        for (const shop of watchedShops) {
            try {
                const shopId = shop.shop_id || shop.username;
                const apiUrl = `https://shopee.vn/api/v4/search/search_items?by=ctime&limit=10&newest=0&order=desc&page_type=shop&scenario=PAGE_OTHERS&shopid=${shopId}&version=2`;
                
                const resp = await fetch(apiUrl, {
                    headers: {
                        "Accept": "application/json",
                        "X-Requested-With": "XMLHttpRequest"
                    }
                });

                if (!resp.ok) continue;
                const json = await resp.json();
                const items = json.items || [];

                for (const raw of items) {
                    const basic = raw.item_basic || raw;
                    const itemId = String(basic.itemid || basic.item_id || "");
                    if (!itemId || knownIds.has(itemId)) continue;

                    // PHÁT HIỆN SẢN PHẨM MỚI TINH!
                    console.log(`🚨 [Phát Hiện Mới] Shop ${shop.name} vừa ra sản phẩm: ${basic.name}`);
                    knownIds.add(itemId);

                    const priceVal = (basic.price || basic.price_min || 0) / 100000;
                    const nowStr = new Date().toLocaleString("vi-VN");
                    const thumb = basic.image ? `https://down-vn.img.susercontent.com/file/${basic.image}` : "";
                    const prodUrl = `https://shopee.vn/product/${basic.shopid || shopId}/${itemId}`;

                    const newProduct = {
                        item_id: itemId,
                        shop_id: String(basic.shopid || shopId),
                        shop_name: shop.name || "Shop Shopee",
                        title: basic.name || "Sản phẩm mới",
                        price: priceVal,
                        price_formatted: Math.round(priceVal).toLocaleString("vi-VN"),
                        historical_sold: basic.historical_sold || 0,
                        created_date: nowStr,
                        product_url: prodUrl,
                        thumb_image: thumb,
                        images: [thumb]
                    };

                    // Lưu vào storage
                    saveNewProductToStorage(newProduct);

                    // Hiển thị thông báo Chrome
                    chrome.notifications.create({
                        type: "basic",
                        iconUrl: "icons/icon48.png",
                        title: "🚨 Shopee: Phát hiện sản phẩm mới!",
                        message: `Shop [${shop.name}] vừa đăng: ${newProduct.title.substring(0, 45)}...`
                    });

                    // BƯỚC 2: TỰ ĐỘNG GỌI API LÀM VIDEO REVIEW NGAY LẬP TỨC
                    if (autoVideo) {
                        triggerAIVideoCreation(newProduct);
                    }
                }
            } catch (err) {
                console.warn(`Lỗi kiểm tra shop ${shop.name}:`, err);
            }
        }

        chrome.storage.local.set({ known_item_ids: Array.from(knownIds) });
    });
}

// Lưu sản phẩm mới vào danh sách
function saveNewProductToStorage(product) {
    chrome.storage.local.get(["scanned_products"], (res) => {
        const list = res.scanned_products || [];
        // Đưa sản phẩm mới lên đầu bảng
        list.unshift(product);
        chrome.storage.local.set({ scanned_products: list });
    });
}

// Gọi API làm Video Review ngay lập tức
async function triggerAIVideoCreation(product) {
    try {
        console.log(`🎬 [BƯỚC 2] Đang gọi API làm video cho: ${product.title}...`);
        const resp = await fetch(API_BACKEND_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                products: [product],
                auto_render: true
            })
        });
        const data = await resp.json();
        if (data.success && data.rendered_videos && data.rendered_videos.length > 0) {
            const vid = data.rendered_videos[0];
            console.log("🎉 [BƯỚC 2 THÀNH CÔNG] Video MP4 đã tạo xong:", vid.video_path);
            chrome.notifications.create({
                type: "basic",
                iconUrl: "icons/icon128.png",
                title: "🎉 BƯỚC 2 HOÀN TẤT: Video AI Sẵn Sàng!",
                message: `Đã làm xong video review cho ${product.title.substring(0, 40)}!`
            });
        }
    } catch (e) {
        console.warn("Backend server chưa bật hoặc lỗi kết nối:", e.message);
    }
}

// Lắng nghe message từ content script hoặc popup
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.action === "TRIGGER_AUTO_VIDEO") {
        triggerAIVideoCreation(msg.product).then(() => {
            sendResponse({ success: true });
        });
        return true;
    } else if (msg.action === "CHECK_NOW") {
        checkWatchedShopsForNewItems().then(() => {
            sendResponse({ success: true });
        });
        return true;
    }
});
