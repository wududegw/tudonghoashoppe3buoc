import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = Path(__file__).resolve().parent / "assets" / "kol_faces"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Bảng màu sắc và thông tin nhận diện cho 10 KOL
KOL_THEMES = [
    ("kol_01", "Hoàng Yến", "Gia Dụng", (255, 107, 107), (255, 230, 230)),
    ("kol_02", "Minh Quân", "Công Nghệ", (78, 115, 223), (224, 235, 255)),
    ("kol_03", "Mai Linh", "Mỹ Phẩm", (246, 135, 179), (255, 235, 245)),
    ("kol_04", "Tuấn Anh", "Thời Trang Nam", (45, 55, 72), (226, 232, 240)),
    ("kol_05", "Quỳnh Anh", "Thời Trang Nữ", (237, 100, 166), (254, 235, 244)),
    ("kol_06", "Bảo Ngọc", "Decor & Chill", (128, 90, 213), (243, 235, 255)),
    ("kol_07", "Thanh Hà", "Mẹ & Bé", (237, 137, 54), (254, 235, 226)),
    ("kol_08", "Đức Thắng", "Thể Thao", (56, 161, 105), (230, 246, 237)),
    ("kol_09", "Hùng Dũng", "Xe & Phụ Tùng", (49, 151, 149), (230, 255, 250)),
    ("kol_10", "Linh Chi", "Săn Sale 1K", (229, 62, 62), (254, 226, 226))
]

def generate_kol_avatars():
    """Tạo sẵn 10 Avatar & Huy hiệu nhận diện chất lượng cao cho 10 KOL."""
    for kol_id, name, tag, primary_color, bg_color in KOL_THEMES:
        avatar_path = ASSETS_DIR / f"{kol_id}.png"
        
        # Tạo ảnh avatar kích thước 400x400 với viền và badge
        size = 400
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Vẽ hình tròn avatar
        margin = 10
        draw.ellipse([margin, margin, size - margin, size - margin], fill=bg_color, outline=primary_color, width=12)

        # Vẽ icon người / placeholder khuôn mặt
        head_radius = 65
        center_x = size // 2
        head_top = 80
        draw.ellipse([center_x - head_radius, head_top, center_x + head_radius, head_top + head_radius * 2], fill=primary_color)
        
        # Thân / Áo
        draw.chord([50, 200, size - 50, size + 100], 0, 360, fill=primary_color)

        # Vẽ huy hiệu tên KOL phía dưới
        badge_h = 60
        badge_y = size - 75
        draw.rounded_rectangle([30, badge_y, size - 30, badge_y + badge_h], radius=20, fill=primary_color)

        # Text tên KOL (vẽ cơ bản không phụ thuộc font hệ thống)
        text_content = f"{name} • {tag}"
        draw.text((center_x, badge_y + badge_h // 2), text_content, fill=(255, 255, 255), anchor="mm")

        img.save(avatar_path, "PNG")
        print(f"✅ Đã tạo sẵn Avatar KOL: {avatar_path}")

if __name__ == "__main__":
    generate_kol_avatars()
