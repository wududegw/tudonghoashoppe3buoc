/**
 * popup.js - Quản lý Shop Watcher & Tự động gọi API làm Video
 */

let productList = [];
let watchedShops = [];

// Chuyển Tab
function switchTab(target) {
    const tabs = ['settings', 'list', 'json'];
    tabs.forEach(t => {
        const view = document.getElementById(`view-${t}`);
        const btn = document.getElementById(`btn-tab-${t}`);
        if (t === target) {
            view.classList.add('active');
            btn.classList.add('active');
        } else {
            view.classList.remove('active');
            btn.classList.remove('active');
        }
    });
}

// Toast
function showToast(msg) {
    const toast = document.getElementById('toast');
    toast.innerText = msg;
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 2500);
}

// Ghi log
function log(msg) {
    const el = document.getElementById('ext-log');
    if (!el) return;
    const time = new Date().toLocaleTimeString();
    el.innerHTML += `<br>[${time}] ${msg}`;
    el.scrollTop = el.scrollHeight;
}

// Tải dữ liệu từ Storage
function loadStoredData() {
    chrome.storage.local.get(["scanned_products", "watched_shops", "ai_provider", "ai_api_key", "auto_video_enabled"], (res) => {
        productList = res.scanned_products || [];
        watchedShops = res.watched_shops || [];

        // Cập nhật số lượng
        document.getElementById('header-count').innerText = productList.length;
        document.getElementById('footer-count-val').innerText = productList.length;

        // Render cấu hình AI
        if (res.ai_provider) document.getElementById('select-ai-provider').value = res.ai_provider;
        if (res.ai_api_key) document.getElementById('input-api-key').value = res.ai_api_key;
        if (res.auto_video_enabled !== undefined) document.getElementById('check-auto-video').checked = res.auto_video_enabled;

        // Render shop đang theo dõi
        renderWatchedShops();

        // Render bảng 6 cột chuẩn
        renderTable(productList);

        // Render JSON
        document.getElementById('json-viewer-content').innerText = JSON.stringify(productList, null, 2);
    });
}

// Render danh sách shop đang theo dõi
function renderWatchedShops() {
    const container = document.getElementById('watched-shops-container');
    if (!watchedShops || watchedShops.length === 0) {
        container.innerHTML = `<span style="font-size: 11px; color: #8a94a6;">Chưa có shop nào. Mở trang Shop Shopee và bấm "+ Theo dõi Tab Hiện Tại"!</span>`;
        return;
    }

    container.innerHTML = watchedShops.map((s, idx) => `
        <div class="shop-pill">
            <span style="color: #00e5ff;">🏬</span>
            <span style="font-weight: 600;">${s.name || s.username}</span>
            <span onclick="removeWatchedShop(${idx})" style="cursor: pointer; color: #ff5252; margin-left: 4px; font-weight: bold;">✕</span>
        </div>
    `).join('');
}

// Xóa shop khỏi theo dõi
window.removeWatchedShop = function(idx) {
    watchedShops.splice(idx, 1);
    chrome.storage.local.set({ watched_shops: watchedShops }, () => {
        renderWatchedShops();
        showToast("Đã xóa shop khỏi danh sách theo dõi!");
    });
};

// Render bảng 6 cột chuẩn
function renderTable(products) {
    const tbody = document.getElementById('table-body');
    if (!products || products.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 40px; color: #8a94a6;">
                    Chưa có sản phẩm nào. Mở một shop Shopee và bấm "Kiểm tra sản phẩm mới & Làm video ngay"!
                </td>
            </tr>`;
        return;
    }

    tbody.innerHTML = products.map((p, idx) => `
        <tr onclick="makeVideoForProduct(${idx})" style="cursor: pointer;" title="Bấm vào dòng này để gọi API làm Video Review cho sản phẩm!">
            <td class="td-shop" title="${p.shop_name || 'Shop Official'}">
                ${p.shop_name || 'Shop Official'}
            </td>
            <td class="td-img">
                <img src="${p.thumb_image || (p.images && p.images[0]) || 'https://via.placeholder.com/60'}" 
                     alt="thumb" 
                     onerror="this.src='https://via.placeholder.com/60'">
            </td>
            <td class="td-title" title="${p.title}">
                <a href="${p.product_url}" target="_blank" onclick="event.stopPropagation();">${p.title}</a>
            </td>
            <td class="td-price">
                ${p.price_formatted || (Math.round(p.price || 0)).toLocaleString('vi-VN')}
            </td>
            <td class="td-sold">
                ${p.historical_sold || 0}
            </td>
            <td class="td-date">
                ${p.created_date || '30/07/2026 18:53:06'}
            </td>
        </tr>
    `).join('');
}

// Gọi làm video cho 1 sản phẩm cụ thể
window.makeVideoForProduct = async function(idx) {
    const p = productList[idx];
    if (!p) return;
    showToast(`Đang gọi API làm video cho: ${p.title.substring(0, 30)}...`);
    log(`[BƯỚC 2] Bắt đầu gọi API làm video cho SP: ${p.title}...`);

    try {
        const res = await fetch("http://localhost:8888/api/auto-video", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ products: [p], auto_render: true })
        });
        const data = await res.json();
        if (data.success && data.rendered_videos && data.rendered_videos.length > 0) {
            const vid = data.rendered_videos[0];
            showToast(`🎉 Đã làm xong video AI: ${vid.video_path}`);
            log(`[Thành công] Video MP4 đã sẵn sàng: ${vid.video_path}`);
        } else {
            showToast(`⚠️ Không tạo được video: ${data.error || 'Kiểm tra backend'}`);
        }
    } catch (e) {
        showToast("Lỗi kết nối máy chủ backend (Port 8888)!");
    }
};

// Theo dõi shop ở Tab Hiện Tại
async function addCurrentShop() {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab || !tab.url || !tab.url.includes("shopee.vn")) {
            showToast("Vui lòng mở một trang Shop Shopee trước!");
            return;
        }

        chrome.tabs.sendMessage(tab.id, { action: "GET_SHOP_INFO" }, (res) => {
            if (res && res.shopName) {
                const info = { name: res.shopName, url: tab.url, username: res.shopName };
                if (!watchedShops.some(s => s.name === info.name)) {
                    watchedShops.push(info);
                    chrome.storage.local.set({ watched_shops: watchedShops }, () => {
                        renderWatchedShops();
                        showToast(`Đã thêm shop [${info.name}] vào danh sách theo dõi!`);
                        log(`[Watcher] Bắt đầu theo dõi shop: ${info.name}`);
                    });
                } else {
                    showToast(`Shop [${info.name}] đã có trong danh sách!`);
                }
            } else {
                showToast("Không nhận diện được Shop. Hãy cuộn xuống để trang tải xong!");
            }
        });
    } catch (e) {
        showToast(`Lỗi: ${e.message}`);
    }
}

// Bắt đầu kiểm tra và làm video ngay
async function triggerCheckAndMakeVideo() {
    const btn = document.getElementById('btn-trigger-scan');
    btn.innerText = "⏳ ĐANG KIỂM TRA SẢN PHẨM MỚI & GỌI API LÀM VIDEO...";
    btn.disabled = true;
    log("[Watcher] Đang quét các Shop được theo dõi để tìm sản phẩm mới...");

    chrome.runtime.sendMessage({ action: "CHECK_NOW" }, (res) => {
        btn.innerText = "⚡ KIỂM TRA SẢN PHẨM MỚI & LÀM VIDEO NGAY";
        btn.disabled = false;
        showToast("Đã kiểm tra xong các shop! Đang cập nhật sản phẩm & video...");
        loadStoredData();
        switchTab('list');
    });
}

// Lưu cấu hình AI API
function saveAIConfig() {
    const provider = document.getElementById('select-ai-provider').value;
    const key = document.getElementById('input-api-key').value.trim();
    const auto = document.getElementById('check-auto-video').checked;

    chrome.storage.local.set({
        ai_provider: provider,
        ai_api_key: key,
        auto_video_enabled: auto
    }, () => {
        showToast("Đã lưu cấu hình AI Video API thành công!");
        log(`[Cấu hình] Provider: ${provider.toUpperCase()}, Tự làm video: ${auto ? 'BẬT' : 'TẮT'}`);
    });
}

// Xuất Excel
function exportExcel() {
    if (productList.length === 0) return showToast("Danh sách đang trống!");
    const header = ["Tên Shop", "Ảnh Thumbnail", "Tên sản phẩm", "Giá (đ)", "Lượt bán", "Ngày Đăng", "Link Shopee"].join('\t');
    const rows = productList.map(p => [
        p.shop_name || 'Shop Official',
        p.thumb_image || '',
        p.title || '',
        p.price_formatted || p.price || '',
        p.historical_sold || 0,
        p.created_date || '',
        p.product_url || ''
    ].join('\t'));
    const text = [header, ...rows].join('\n');
    navigator.clipboard.writeText(text).then(() => showToast("Đã sao chép định dạng Excel vào Clipboard!"));
}

// Xuất JSON
function exportJSON() {
    if (productList.length === 0) return showToast("Danh sách đang trống!");
    navigator.clipboard.writeText(JSON.stringify(productList, null, 2)).then(() => showToast("Đã sao chép dữ liệu JSON!"));
}

// Tải file CSV
function downloadCSV() {
    if (productList.length === 0) return showToast("Danh sách đang trống!");
    let csvContent = "\uFEFFTên Shop,Ảnh,Tên sản phẩm,Giá (đ),Lượt bán,Ngày Đăng,Link Shopee\n";
    productList.forEach(p => {
        const row = [
            `"${(p.shop_name || '').replace(/"/g, '""')}"`,
            `"${(p.thumb_image || '').replace(/"/g, '""')}"`,
            `"${(p.title || '').replace(/"/g, '""')}"`,
            `"${p.price_formatted || p.price || 0}"`,
            `"${p.historical_sold || 0}"`,
            `"${p.created_date || ''}"`,
            `"${p.product_url || ''}"`
        ];
        csvContent += row.join(",") + "\n";
    });

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `shopee_products_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("Đã tải file CSV thành công!");
}

document.addEventListener('DOMContentLoaded', () => {
    // Tabs
    document.getElementById('btn-tab-settings').addEventListener('click', () => switchTab('settings'));
    document.getElementById('btn-tab-list').addEventListener('click', () => switchTab('list'));
    document.getElementById('btn-tab-json').addEventListener('click', () => switchTab('json'));

    // Actions
    document.getElementById('btn-open-shopee-tab').addEventListener('click', () => chrome.tabs.create({ url: 'https://shopee.vn' }));
    document.getElementById('btn-add-current-shop').addEventListener('click', addCurrentShop);
    document.getElementById('btn-trigger-scan').addEventListener('click', triggerCheckAndMakeVideo);
    document.getElementById('btn-save-key').addEventListener('click', saveAIConfig);
    document.getElementById('check-auto-video').addEventListener('change', saveAIConfig);

    document.getElementById('btn-refresh-list').addEventListener('click', () => {
        loadStoredData();
        showToast("Đã làm mới danh sách!");
    });

    document.getElementById('btn-clear-data').addEventListener('click', () => {
        if (confirm("Bạn có chắc muốn xóa danh sách sản phẩm không?")) {
            chrome.storage.local.set({ scanned_products: [] }, () => {
                loadStoredData();
                showToast("Đã xóa sạch dữ liệu!");
            });
        }
    });

    document.getElementById('btn-export-excel').addEventListener('click', exportExcel);
    document.getElementById('btn-export-json').addEventListener('click', exportJSON);
    document.getElementById('btn-download-csv').addEventListener('click', downloadCSV);

    loadStoredData();
    switchTab('list');
});
