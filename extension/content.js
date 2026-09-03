/**
 * content.js - Tự động theo dõi Shop Shopee, phát hiện sản phẩm mới và kích hoạt Bước 2 làm video AI luôn
 */

(function() {
    console.log("[Shopee Shop Watcher] Content script đã kích hoạt!");

    function getShopInfo() {
        const shopEl = document.querySelector("div.section-seller-overview-horizontal__portrait-name, h1.page-title, div[data-sqe='name']");
        const shopName = (shopEl && shopEl.innerText.trim()) || "Shop Shopee";
        
        let username = "";
        const path = window.location.pathname.replace(/^\/+|\/+$/g, '');
        const parts = path.split('/');
        if (parts.length > 0 && !['search', 'cart', 'buyer', 'user', 'flash_sale'].includes(parts[0])) {
            username = parts[0];
        }

        // Tìm shopId từ HTML
        let shopId = "87261521";
        const m = document.documentElement.innerHTML.match(/"shopid"\s*:\s*(\d+)/);
        if (m) shopId = m[1];

        return { name: shopName, username: username || shopName, shop_id: shopId, url: window.location.href };
    }

    // 1. Tạo Widget Nổi: Nút Quét & Nút Theo Dõi Shop
    function injectFloatingWidget() {
        if (document.getElementById("shopee-watcher-widget")) return;

        const widget = document.createElement("div");
        widget.id = "shopee-watcher-widget";
        widget.style.cssText = `
            position: fixed; bottom: 25px; right: 25px; z-index: 9999999;
            display: flex; flex-direction: column; gap: 8px; align-items: flex-end;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            user-select: none;
        `;

        widget.innerHTML = `
            <div id="btn-watch-shop" style="display: flex; align-items: center; gap: 6px; background: #181b24; color: #00e5ff; padding: 8px 14px; border-radius: 30px; font-size: 11px; font-weight: bold; border: 1px solid #00e5ff; cursor: pointer; box-shadow: 0 4px 15px rgba(0,0,0,0.4); transition: all 0.2s;">
                <span id="watch-icon">🔔</span>
                <span id="watch-text">THEO DÕI SHOP NÀY</span>
            </div>

            <div id="btn-scan-and-video" style="display: flex; align-items: center; gap: 8px; background: linear-gradient(135deg, #ee4d2d, #ff5722); color: #fff; padding: 12px 18px; border-radius: 50px; box-shadow: 0 8px 25px rgba(238, 77, 45, 0.4); cursor: pointer; font-size: 12px; font-weight: bold; border: 2px solid #fff; transition: transform 0.2s;">
                <span>⚡ QUÉT & TỰ ĐỘNG LÀM VIDEO AI</span>
                <span id="crawler-count-badge" style="background: #fff; color: #ee4d2d; border-radius: 10px; padding: 1px 6px; font-size: 11px;">0</span>
            </div>
        `;

        document.body.appendChild(widget);

        // Xử lý nút Theo Dõi Shop
        const btnWatch = document.getElementById("btn-watch-shop");
        btnWatch.addEventListener("click", () => {
            const info = getShopInfo();
            chrome.storage.local.get(["watched_shops"], (res) => {
                const list = res.watched_shops || [];
                const exists = list.some(s => s.username === info.username || s.shop_id === info.shop_id);
                if (!exists) {
                    list.push(info);
                    chrome.storage.local.set({ watched_shops: list });
                    showShopeeToast(`Đã thêm shop [${info.name}] vào danh sách theo dõi tự động!`);
                    document.getElementById("watch-text").innerText = "ĐANG THEO DÕI SHOP";
                    document.getElementById("watch-icon").innerText = "✅";
                } else {
                    showShopeeToast(`Shop [${info.name}] đã có trong danh sách theo dõi!`);
                }
            });
        });

        // Xử lý nút Quét & Làm Video
        const btnScan = document.getElementById("btn-scan-and-video");
        btnScan.addEventListener("click", async () => {
            btnScan.style.transform = "scale(0.95)";
            setTimeout(() => btnScan.style.transform = "scale(1)", 150);
            await autoScanAndGenerateVideo();
        });

        updateBadge();
        checkIfShopAlreadyWatched();
    }

    // Kiểm tra xem shop hiện tại đã được theo dõi chưa
    function checkIfShopAlreadyWatched() {
        const info = getShopInfo();
        chrome.storage.local.get(["watched_shops"], (res) => {
            const list = res.watched_shops || [];
            if (list.some(s => s.username === info.username || s.shop_id === info.shop_id)) {
                const txt = document.getElementById("watch-text");
                const ico = document.getElementById("watch-icon");
                if (txt) txt.innerText = "ĐANG THEO DÕI SHOP";
                if (ico) ico.innerText = "✅";
            }
        });
    }

    function updateBadge() {
        chrome.storage.local.get(["scanned_products"], (res) => {
            const count = (res.scanned_products || []).length;
            const badge = document.getElementById("crawler-count-badge");
            if (badge) badge.innerText = count;
        });
    }

    function showShopeeToast(msg, isSuccess = true) {
        let toast = document.getElementById("shopee-watcher-toast");
        if (!toast) {
            toast = document.createElement("div");
            toast.id = "shopee-watcher-toast";
            toast.style.cssText = `
                position: fixed; top: 25px; right: 25px; z-index: 99999999;
                background: #181b24; color: #fff; border: 2px solid #00e5ff;
                padding: 12px 18px; border-radius: 8px; font-size: 13px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5); transition: all 0.3s;
                transform: translateY(-20px); opacity: 0; display: flex; align-items: center; gap: 8px;
            `;
            document.body.appendChild(toast);
        }

        toast.innerHTML = `<span>${isSuccess ? '🔔' : '⚠️'}</span> <span>${msg}</span>`;
        toast.style.transform = "translateY(0)";
        toast.style.opacity = "1";

        setTimeout(() => {
            toast.style.transform = "translateY(-20px)";
            toast.style.opacity = "0";
        }, 4000);
    }

    // Trích xuất toàn bộ sản phẩm trên trang
    function extractProducts() {
        const info = getShopInfo();
        const items = [];
        const seen = new Set();

        const cards = document.querySelectorAll("div.shop-search-result-view__item, li.shopee-search-item-result__item, div[data-sqe='item'], a[data-sqe='link']");
        const nowStr = new Date().toLocaleString("vi-VN");

        cards.forEach((card, idx) => {
            try {
                const link = card.tagName === 'A' ? card : card.querySelector("a");
                if (!link) return;
                const href = link.getAttribute("href") || "";
                if (!href) return;
                const fullUrl = href.startsWith("http") ? href : `https://shopee.vn${href}`;

                let itemId = "";
                const m = fullUrl.match(/i\.(\d+)\.(\d+)/) || fullUrl.match(/product\/(\d+)\/(\d+)/);
                itemId = m ? m[2] : `prod_${idx}_${Date.now()}`;
                if (seen.has(itemId)) return;
                seen.add(itemId);

                const titleEl = card.querySelector("div[data-sqe='name'], div.line-clamp-2, div.whitespace-normal");
                const title = titleEl ? titleEl.innerText.trim() : (link.getAttribute("title") || "Sản phẩm Shopee");
                if (!title || title.length < 3) return;

                let priceFormatted = "150.000";
                let rawPrice = 150000;
                const priceEl = card.querySelector("span.font-medium, span:has-text('₫')");
                if (priceEl) {
                    const digits = priceEl.innerText.replace("₫", "").replace(/\./g, "").replace(/,/g, "").trim();
                    if (/^\d+$/.test(digits)) {
                        rawPrice = parseInt(digits, 10);
                        priceFormatted = rawPrice.toLocaleString("vi-VN");
                    }
                }

                let sold = 0;
                const soldEl = card.querySelector("div:has-text('Đã bán')");
                if (soldEl) {
                    const mSold = soldEl.innerText.match(/[\d,.]+/);
                    if (mSold) sold = parseInt(mSold[0].replace(/\./g, ""), 10) || 0;
                }

                const img = card.querySelector("img");
                let thumb = img ? (img.getAttribute("src") || img.getAttribute("data-src") || "") : "";
                if (!thumb || thumb.startsWith("data:")) thumb = "https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lsi5o1k47l73ba";

                items.push({
                    item_id: itemId,
                    shop_id: info.shop_id,
                    shop_name: info.name,
                    title: title,
                    price: rawPrice,
                    price_formatted: priceFormatted,
                    historical_sold: sold,
                    created_date: nowStr,
                    product_url: fullUrl,
                    thumb_image: thumb,
                    images: [thumb]
                });
            } catch (e) {}
        });

        return items;
    }

    // Quét và tự động gọi Bước 2 làm video
    async function autoScanAndGenerateVideo() {
        const btnBadge = document.querySelector("#btn-scan-and-video span:first-child");
        if (btnBadge) btnBadge.innerText = "⏳ ĐANG CUỘN TRANG...";

        // Cuộn trang lấy toàn bộ dữ liệu
        for (let i = 1; i <= 5; i++) {
            window.scrollTo({ top: (document.body.scrollHeight / 5) * i, behavior: 'smooth' });
            await new Promise(r => setTimeout(r, 500));
        }
        window.scrollTo({ top: 0, behavior: 'smooth' });
        await new Promise(r => setTimeout(r, 400));

        const products = extractProducts();
        if (products.length === 0) {
            showShopeeToast("Không tìm thấy sản phẩm trên trang này!", false);
            if (btnBadge) btnBadge.innerText = "⚡ QUÉT & TỰ ĐỘNG LÀM VIDEO AI";
            return;
        }

        // Lưu vào Storage và cập nhật known_item_ids
        chrome.storage.local.get(["scanned_products", "known_item_ids"], (res) => {
            const list = res.scanned_products || [];
            const known = new Set(res.known_item_ids || []);
            const map = new Map();
            list.forEach(p => map.set(p.item_id, p));
            products.forEach(p => {
                map.set(p.item_id, p);
                known.add(p.item_id);
            });
            chrome.storage.local.set({
                scanned_products: Array.from(map.values()),
                known_item_ids: Array.from(known)
            }, updateBadge);
        });

        // BƯỚC 2: GỌI API LÀM VIDEO LUÔN CHO SẢN PHẨM MỚI NHẤT
        if (btnBadge) btnBadge.innerText = "🎬 ĐANG GỌI API LÀM VIDEO...";
        showShopeeToast(`Đã lấy link & ảnh của ${products.length} sản phẩm. Đang gọi API làm video review luôn...`);

        try {
            const resp = await fetch("http://localhost:8888/api/auto-video", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    products: products,
                    auto_render: true
                })
            });
            const data = await resp.json();
            if (data.success && data.rendered_videos && data.rendered_videos.length > 0) {
                const vid = data.rendered_videos[0];
                showShopeeToast(`🎉 BƯỚC 2 XONG! Đã làm xong video review cho ${vid.title.substring(0, 35)}...`);
                if (btnBadge) btnBadge.innerText = "✅ ĐÃ LÀM VIDEO XONG!";
            } else {
                showShopeeToast(`Đã quét xong ${products.length} sản phẩm!`);
                if (btnBadge) btnBadge.innerText = `ĐÃ QUÉT (${products.length})`;
            }
        } catch (e) {
            showShopeeToast(`Đã lưu ${products.length} sản phẩm vào Extension!`);
            if (btnBadge) btnBadge.innerText = `ĐÃ QUÉT (${products.length})`;
        }

        setTimeout(() => {
            if (btnBadge) btnBadge.innerText = "⚡ QUÉT & TỰ ĐỘNG LÀM VIDEO AI";
        }, 3000);
    }

    // Tự động kiểm tra định kỳ 30s trên trang shop nếu đang mở
    setInterval(() => {
        const info = getShopInfo();
        chrome.storage.local.get(["watched_shops", "known_item_ids", "auto_video_enabled"], (data) => {
            const watched = data.watched_shops || [];
            if (!watched.some(s => s.username === info.username || s.shop_id === info.shop_id)) return;

            const current = extractProducts();
            const known = new Set(data.known_item_ids || []);
            const brandNew = current.filter(p => !known.has(p.item_id));

            if (brandNew.length > 0) {
                const firstNew = brandNew[0];
                console.log("🚨 [Auto Watcher] Phát hiện sản phẩm mới:", firstNew.title);
                brandNew.forEach(p => known.add(p.item_id));
                chrome.storage.local.set({ known_item_ids: Array.from(known) });

                showShopeeToast(`🚨 SẢN PHẨM MỚI TỪ SHOP: ${firstNew.title.substring(0, 35)}... Đang làm video review luôn!`);

                // Gọi làm video luôn
                fetch("http://localhost:8888/api/auto-video", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ products: brandNew, auto_render: true })
                });
            }
        });
    }, 30000);

    window.addEventListener("load", () => setTimeout(injectFloatingWidget, 1500));
    if (document.readyState === "complete" || document.readyState === "interactive") {
        setTimeout(injectFloatingWidget, 1000);
    }
})();
