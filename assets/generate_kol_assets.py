import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = Path(__file__).resolve().parent / "kol_faces"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Bảng màu sắc và thông tin nhận diện cho 10 KOL
KOL_THEMES = [
    ("kol_01", "Hoàng Yến", "Gia Dụng", (255, 107, 107), (255, 230, 230), "female"),
    ("kol_02", "Minh Quân", "Công Nghệ", (78, 115, 223), (224, 235, 255), "male"),
    ("kol_03", "Mai Linh", "Mỹ Phẩm", (246, 135, 179), (255, 235, 245), "female"),
    ("kol_04", "Tuấn Anh", "Thời Trang Nam", (45, 55, 72), (226, 232, 240), "male"),
    ("kol_05", "Quỳnh Anh", "Thời Trang Nữ", (237, 100, 166), (254, 235, 244), "female"),
    ("kol_06", "Bảo Ngọc", "Decor & Chill", (128, 90, 213), (243, 235, 255), "female"),
    ("kol_07", "Thanh Hà", "Mẹ & Bé", (237, 137, 54), (254, 235, 226), "female"),
    ("kol_08", "Đức Thắng", "Thể Thao", (56, 161, 105), (230, 246, 237), "male"),
    ("kol_09", "Hùng Dũng", "Xe & Phụ Tùng", (49, 151, 149), (230, 255, 250), "male"),
    ("kol_10", "Linh Chi", "Săn Sale 1K", (229, 62, 62), (254, 226, 226), "female")
]

def generate_kol_avatars():
    """Tạo sẵn 10 Avatar & Huy hiệu nhận diện sắc nét cho 10 KOL."""
    for kol_id, name, tag, primary_color, bg_color, gender in KOL_THEMES:
        avatar_path = ASSETS_DIR / f"{kol_id}.png"
        
        size = 400
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Viền ngoài phát sáng
        margin = 10
        draw.ellipse([margin, margin, size - margin, size - margin], fill=bg_color, outline=primary_color, width=12)

        # Tóc sau nếu là nữ
        hair_color = (45, 30, 25)
        if gender == "female":
            draw.chord([55, 70, size - 55, 360], 0, 360, fill=hair_color)

        # Khuôn mặt & thân áo
        skin_color = (255, 224, 195) if gender == "female" else (245, 210, 180)
        center_x = size // 2
        
        # Cổ & thân
        draw.rectangle([center_x - 30, 190, center_x + 30, 250], fill=skin_color)
        draw.chord([40, 220, size - 40, size + 110], 0, 360, fill=primary_color)

        # Mặt
        draw.ellipse([center_x - 65, 80, center_x + 65, 220], fill=skin_color)

        # Mắt
        eye_y = 140
        draw.ellipse([center_x - 38, eye_y, center_x - 22, eye_y + 12], fill=(30, 30, 30))
        draw.ellipse([center_x + 22, eye_y, center_x + 38, eye_y + 12], fill=(30, 30, 30))
        draw.line([center_x - 42, eye_y - 8, center_x - 18, eye_y - 12], fill=hair_color, width=3)
        draw.line([center_x + 18, eye_y - 12, center_x + 42, eye_y - 8], fill=hair_color, width=3)

        # Tóc trước
        draw.chord([center_x - 70, 65, center_x + 70, 140], 180, 360, fill=hair_color)

        # Miệng cười
        draw.arc([center_x - 18, 175, center_x + 18, 195], 0, 180, fill=(180, 50, 50), width=4)

        # Badge tên KOL phía dưới
        badge_h = 56
        badge_y = size - 75
        draw.rounded_rectangle([25, badge_y, size - 25, badge_y + badge_h], radius=16, fill=primary_color)

        text_content = f"{name} • {tag}"
        draw.text((center_x, badge_y + badge_h // 2), text_content, fill=(255, 255, 255), anchor="mm")

        img.save(avatar_path, "PNG")
        print(f"✅ Đã tạo Avatar KOL: {avatar_path}")

if __name__ == "__main__":
    generate_kol_avatars()
