"""
utils/image_manager.py
======================
Jewellery Image Manager
- Creates static/images/jewelry/ category library
- Generates high-quality jewellery images using PIL
- Assigns correct images to all inventory products
- Ensures AI Recommendations use the same images
"""

import os
import sqlite3
import math

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ── Colour palette ──────────────────────────────────────────────────────────
BG         = (13,  13,  22)      # near-black background
GOLD       = (212, 175, 55)      # classic gold
GOLD_LIGHT = (255, 232, 158)     # bright highlight
GOLD_DARK  = (160, 120, 20)      # shadow
PLATINUM   = (200, 208, 220)
WHITE_GOLD = (230, 230, 240)
SILVER     = (192, 192, 210)
DIAMOND    = (220, 240, 255)
ROSE_GOLD  = (235, 170, 130)


def _load_font(size: int):
    """Load a font; fall back to PIL default."""
    for name in ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "Roboto-Regular.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def _draw_shine(draw, cx, cy, r, color=GOLD_LIGHT, n=6):
    """Draw sparkle/shine star at (cx, cy)."""
    for i in range(n * 2):
        angle = math.pi * 2 * i / (n * 2)
        length = r if i % 2 == 0 else r * 0.4
        ex = cx + math.cos(angle) * length
        ey = cy + math.sin(angle) * length
        if i == 0:
            pts = [(cx, cy)]
        pts.append((ex, ey))
    draw.polygon(pts[:n*2+1], fill=color)


def _draw_diamond_gem(draw, cx, cy, size=18, color=DIAMOND):
    """Draw a simplified diamond shape."""
    half = size // 2
    # table (top flat)
    draw.polygon([
        (cx - half * 0.6, cy - half * 0.3),
        (cx + half * 0.6, cy - half * 0.3),
        (cx + half * 0.5, cy - half * 0.7),
        (cx - half * 0.5, cy - half * 0.7),
    ], fill=color, outline=GOLD)
    # pavilion (bottom point)
    draw.polygon([
        (cx - half * 0.6, cy - half * 0.3),
        (cx + half * 0.6, cy - half * 0.3),
        (cx, cy + half * 0.9),
    ], fill=(*color[:3], 180), outline=GOLD)
    # highlight
    draw.line([(cx - half * 0.3, cy - half * 0.6), (cx - half * 0.05, cy - half * 0.35)],
              fill=(255, 255, 255), width=2)


def _draw_label(draw, text, sub, W, H, font_l, font_s, color=GOLD):
    """Draw centred product name + subtitle at bottom."""
    # semi-transparent bar
    draw.rectangle([0, H - 72, W, H], fill=(8, 8, 15, 200))
    bbox = draw.textbbox((0, 0), text, font=font_l)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, H - 62), text, fill=color, font=font_l)
    bbox2 = draw.textbbox((0, 0), sub, font=font_s)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((W - tw2) // 2, H - 38), sub, fill=(180, 150, 60), font=font_s)


# ── Individual category image generators ────────────────────────────────────

def _make_ring(path, name="Gold Ring", material="Gold", style="plain"):
    W, H = 480, 380
    img = Image.new("RGBA", (W, H), BG + (255,))
    draw = ImageDraw.Draw(img, "RGBA")
    cx, cy = W // 2, H // 2 - 20
    R_out, R_in = 90, 62

    ring_color = {"platinum": PLATINUM, "rose gold": ROSE_GOLD,
                  "white gold": WHITE_GOLD, "silver": SILVER}.get(material.lower(), GOLD)
    light_c = tuple(min(255, v + 60) for v in ring_color)
    dark_c  = tuple(max(0,   v - 60) for v in ring_color)

    # Outer ring ellipse
    draw.ellipse([cx - R_out, cy - R_out // 2, cx + R_out, cy + R_out // 2],
                 fill=dark_c, outline=ring_color, width=5)
    # Inner hole
    draw.ellipse([cx - R_in, cy - R_in // 2, cx + R_in, cy + R_in // 2],
                 fill=BG + (255,))

    # Gradient highlight arc
    for t in range(0, 120, 3):
        rad = math.radians(t - 60)
        hx = cx + math.cos(rad) * (R_out - 10)
        hy = cy + math.sin(rad) * ((R_out - 10) // 2)
        alpha = int(180 * abs(math.cos(math.radians(t - 60))))
        draw.ellipse([hx - 4, hy - 3, hx + 4, hy + 3], fill=light_c + (alpha,))

    # Diamond solitaire for diamond rings
    if "diamond" in name.lower() or "solitaire" in name.lower() or "eternity" in name.lower():
        _draw_diamond_gem(draw, cx, cy - R_out // 2 - 16, size=32)
        for dx, dy in [(-25, -10), (25, -10), (0, -8)]:
            _draw_diamond_gem(draw, cx + dx, cy - R_out // 2 - 12 + dy, size=14)
    elif "kundan" in name.lower():
        # Kundan gems around the top
        for i, angle in enumerate(range(-60, 61, 20)):
            rad = math.radians(angle)
            gx = cx + math.cos(rad) * (R_out - 8)
            gy = cy + math.sin(rad) * ((R_out - 8) // 2) - 2
            draw.ellipse([gx - 5, gy - 5, gx + 5, gy + 5], fill=(200, 50, 50), outline=GOLD, width=1)
    else:
        # simple gold beads at top
        for angle in range(-60, 61, 20):
            rad = math.radians(angle)
            gx = cx + math.cos(rad) * (R_out - 5)
            gy = cy + math.sin(rad) * ((R_out - 5) // 2)
            draw.ellipse([gx - 4, gy - 3, gx + 4, gy + 3], fill=GOLD_LIGHT, outline=GOLD)

    # Sparkles
    for sx, sy in [(cx + 110, cy - 60), (cx - 100, cy - 80), (cx + 40, cy - 110)]:
        _draw_shine(draw, sx, sy, 8, GOLD_LIGHT)

    font_l = _load_font(20)
    font_s = _load_font(13)
    _draw_label(draw, name, f"{material}  •  Fine Jewellery", W, H, font_l, font_s)
    img.convert("RGB").save(path, "WEBP", quality=88)


def _make_necklace(path, name="Gold Necklace", material="Gold"):
    W, H = 480, 380
    img = Image.new("RGBA", (W, H), BG + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    nc = {"platinum": PLATINUM, "rose gold": ROSE_GOLD, "white gold": WHITE_GOLD,
          "silver": SILVER}.get(material.lower(), GOLD)
    lc = tuple(min(255, v + 50) for v in nc)

    cx = W // 2
    # Main necklace arc
    for t in range(0, 181, 2):
        rad = math.radians(t)
        x = cx + math.cos(rad) * 155
        y = 90 + math.sin(rad) * 100
        r = 5 if 85 <= t <= 95 else 4
        draw.ellipse([x - r, y - r, x + r, y + r], fill=nc, outline=lc, width=1)

    # Chain beads
    for t in range(0, 181, 8):
        rad = math.radians(t)
        x = cx + math.cos(rad) * 155
        y = 90 + math.sin(rad) * 100
        draw.ellipse([x - 6, y - 6, x + 6, y + 6], fill=lc, outline=nc, width=1)

    # Pendant / centre-piece
    px, py = cx, 90 + 100 + 15  # bottom of arc

    if "diamond" in name.lower() or "royal" in name.lower():
        # Diamond cluster pendant
        _draw_diamond_gem(draw, px, py, size=38)
        for dx, dy in [(-20, -8), (20, -8), (-12, 18), (12, 18)]:
            _draw_diamond_gem(draw, px + dx, py + dy, size=18)
    elif "kundan" in name.lower():
        draw.ellipse([px - 22, py - 22, px + 22, py + 22], fill=(185, 30, 30), outline=GOLD, width=3)
        draw.ellipse([px - 12, py - 12, px + 12, py + 12], fill=(220, 180, 0))
        for a in range(0, 360, 45):
            r2 = math.radians(a)
            draw.ellipse([px + math.cos(r2)*18 - 4, py + math.sin(r2)*18 - 4,
                          px + math.cos(r2)*18 + 4, py + math.sin(r2)*18 + 4], fill=(180, 30, 30))
    elif "temple" in name.lower():
        # Temple pendant with peacock motif
        draw.polygon([(px, py - 30), (px + 20, py), (px + 12, py + 30),
                      (px - 12, py + 30), (px - 20, py)], fill=nc, outline=lc, width=2)
        draw.ellipse([px - 8, py - 8, px + 8, py + 8], fill=lc)
    elif "mangalsutra" in name.lower():
        # Black beads + gold
        for i, bx in enumerate(range(px - 40, px + 50, 14)):
            color = (20, 20, 20) if i % 3 != 0 else nc
            draw.ellipse([bx - 6, py - 6, bx + 6, py + 6], fill=color, outline=nc)
        draw.polygon([(px, py + 10), (px + 14, py + 32), (px - 14, py + 32)], fill=nc, outline=lc, width=2)
    else:
        # Classic drop pendant
        draw.rectangle([px - 3, py - 20, px + 3, py], fill=nc)
        draw.ellipse([px - 18, py, px + 18, py + 36], fill=nc, outline=lc, width=2)
        draw.ellipse([px - 9, py + 9, px + 9, py + 27], fill=lc)

    # Sparkles
    for sx, sy in [(cx - 130, 60), (cx + 130, 60), (cx, 40)]:
        _draw_shine(draw, sx, sy, 7, GOLD_LIGHT)

    font_l = _load_font(20)
    font_s = _load_font(13)
    _draw_label(draw, name, f"{material}  •  Fine Jewellery", W, H, font_l, font_s)
    img.convert("RGB").save(path, "WEBP", quality=88)


def _make_bracelet(path, name="Gold Bracelet", material="Gold"):
    W, H = 480, 380
    img = Image.new("RGBA", (W, H), BG + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    bc = {"platinum": PLATINUM, "rose gold": ROSE_GOLD, "white gold": WHITE_GOLD,
          "silver": SILVER}.get(material.lower(), GOLD)
    lc = tuple(min(255, v + 60) for v in bc)
    cx, cy = W // 2, H // 2 - 10

    is_bangle = any(k in name.lower() for k in ["bangle", "kada", "bangles"])
    is_diamond = "diamond" in name.lower()

    if is_bangle:
        # Solid bangle
        Rx, Ry = 120, 45
        draw.ellipse([cx - Rx, cy - Ry, cx + Rx, cy + Ry], fill=bc, outline=lc, width=8)
        draw.ellipse([cx - Rx + 15, cy - Ry + 12, cx + Rx - 15, cy + Ry - 12], fill=BG + (255,))
        # decorative grooves
        for r_off in [-4, 0, 4]:
            draw.ellipse([cx - Rx + r_off, cy - Ry + r_off // 2,
                          cx + Rx - r_off, cy + Ry - r_off // 2],
                         outline=lc, width=1)
        if is_diamond:
            for angle in range(0, 181, 30):
                rad = math.radians(angle)
                gx = cx + math.cos(rad) * Rx
                gy = cy - math.sin(rad) * Ry
                _draw_diamond_gem(draw, int(gx), int(gy), size=14)
        else:
            # gold beads
            for angle in range(0, 360, 20):
                rad = math.radians(angle)
                gx = cx + math.cos(rad) * (Rx - 6)
                gy = cy + math.sin(rad) * (Ry - 4)
                draw.ellipse([gx - 4, gy - 3, gx + 4, gy + 3], fill=lc, outline=bc)
    else:
        # Flexible link bracelet
        for i, x in enumerate(range(cx - 130, cx + 135, 22)):
            c = lc if i % 2 == 0 else bc
            draw.rounded_rectangle([x - 10, cy - 14, x + 10, cy + 14], radius=5, fill=c, outline=bc, width=2)
            if is_diamond and i % 2 == 0:
                _draw_diamond_gem(draw, x, cy, size=12)
        # clasp
        draw.ellipse([cx + 125, cy - 8, cx + 141, cy + 8], fill=lc, outline=bc, width=2)

    for sx, sy in [(cx - 140, cy - 80), (cx + 140, cy - 80), (cx, cy - 100)]:
        _draw_shine(draw, sx, sy, 7, GOLD_LIGHT)

    font_l = _load_font(20)
    font_s = _load_font(13)
    _draw_label(draw, name, f"{material}  •  Fine Jewellery", W, H, font_l, font_s)
    img.convert("RGB").save(path, "WEBP", quality=88)


def _make_earrings(path, name="Gold Earrings", material="Gold"):
    W, H = 480, 380
    img = Image.new("RGBA", (W, H), BG + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    ec = {"platinum": PLATINUM, "rose gold": ROSE_GOLD, "white gold": WHITE_GOLD,
          "silver": SILVER}.get(material.lower(), GOLD)
    lc = tuple(min(255, v + 60) for v in ec)

    is_jhumka = "jhumka" in name.lower()
    is_drop   = "drop" in name.lower() or "pearl" in name.lower()
    is_diamond = "diamond" in name.lower() or "luxury" in name.lower()

    # Draw left + right earring
    for cx, label in [(W // 2 - 80, "L"), (W // 2 + 80, "R")]:
        top_y = 70

        # Hook
        draw.arc([cx - 12, top_y - 20, cx + 12, top_y + 10], start=200, end=360,
                 fill=ec, width=3)
        draw.line([cx + 12, top_y - 5, cx + 12, top_y + 5], fill=ec, width=3)

        # Top stud / gem
        if is_diamond:
            _draw_diamond_gem(draw, cx, top_y + 8, size=22)
        else:
            draw.ellipse([cx - 10, top_y, cx + 10, top_y + 20], fill=ec, outline=lc, width=2)

        if is_jhumka:
            # Jhumka bell
            by = top_y + 30
            # dome
            draw.arc([cx - 30, by, cx + 30, by + 40], start=180, end=360, fill=ec, width=4)
            draw.ellipse([cx - 30, by + 18, cx + 30, by + 58], fill=ec, outline=lc, width=2)
            # small beads at bottom
            for dx in range(-24, 28, 8):
                draw.ellipse([cx + dx - 4, by + 54, cx + dx + 4, by + 62],
                             fill=lc, outline=ec, width=1)
            # tiny dangles
            for dx in [-20, -8, 0, 8, 20]:
                draw.line([cx + dx, by + 62, cx + dx, by + 75], fill=ec, width=1)
                draw.ellipse([cx + dx - 3, by + 73, cx + dx + 3, by + 80], fill=lc)

        elif is_drop:
            # Pearl drop
            draw.line([cx, top_y + 20, cx, top_y + 55], fill=ec, width=2)
            pearl_c = (240, 240, 245)  # pearl white
            draw.ellipse([cx - 20, top_y + 55, cx + 20, top_y + 95],
                         fill=pearl_c, outline=ec, width=2)
            draw.ellipse([cx - 7, top_y + 60, cx - 2, top_y + 67],
                         fill=(255, 255, 255))  # highlight

        elif is_diamond:
            # Diamond drops
            for i, dy in enumerate([35, 65, 95]):
                sz = 22 - i * 4
                _draw_diamond_gem(draw, cx, top_y + dy, size=sz)
        else:
            # Classic dangle
            draw.line([cx, top_y + 20, cx, top_y + 50], fill=ec, width=2)
            draw.polygon([(cx, top_y + 50), (cx + 16, top_y + 70),
                          (cx, top_y + 90), (cx - 16, top_y + 70)],
                         fill=ec, outline=lc, width=2)
            draw.ellipse([cx - 7, top_y + 66, cx + 7, top_y + 80], fill=lc)

    for sx, sy in [(W // 2, 30), (W // 2 - 140, 50), (W // 2 + 140, 50)]:
        _draw_shine(draw, sx, sy, 7, GOLD_LIGHT)

    font_l = _load_font(20)
    font_s = _load_font(13)
    _draw_label(draw, name, f"{material}  •  Fine Jewellery", W, H, font_l, font_s)
    img.convert("RGB").save(path, "WEBP", quality=88)


def _make_pendant(path, name="Diamond Pendant", material="Gold"):
    W, H = 480, 380
    img = Image.new("RGBA", (W, H), BG + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    pc = {"platinum": PLATINUM, "rose gold": ROSE_GOLD, "white gold": WHITE_GOLD,
          "silver": SILVER}.get(material.lower(), GOLD)
    lc = tuple(min(255, v + 60) for v in pc)

    cx, cy = W // 2, H // 2

    # Chain
    for bx in range(40, W - 40, 16):
        draw.ellipse([bx - 6, 70 - 3, bx + 6, 70 + 3], fill=pc, outline=lc, width=1)
    # bail (loop connecting chain to pendant)
    draw.arc([cx - 10, 58, cx + 10, 90], start=0, end=180, fill=pc, width=4)

    # Pendant body
    if "diamond" in name.lower() or "elegant" in name.lower():
        # Large diamond solitaire pendant
        _draw_diamond_gem(draw, cx, cy, size=64)
        for dx, dy in [(-28, -20), (28, -20), (-20, 26), (20, 26)]:
            _draw_diamond_gem(draw, cx + dx, cy + dy, size=22)
        # halo dots
        for angle in range(0, 360, 22):
            rad = math.radians(angle)
            draw.ellipse([cx + math.cos(rad)*42 - 4, cy + math.sin(rad)*42 - 4,
                          cx + math.cos(rad)*42 + 4, cy + math.sin(rad)*42 + 4],
                         fill=DIAMOND, outline=pc, width=1)
    else:
        # Teardrop pendant
        draw.ellipse([cx - 26, cy - 30, cx + 26, cy + 20], fill=pc, outline=lc, width=3)
        draw.polygon([(cx - 26, cy + 8), (cx + 26, cy + 8), (cx, cy + 55)],
                     fill=pc, outline=lc, width=2)
        draw.ellipse([cx - 12, cy - 18, cx + 12, cy + 8], fill=lc)

    for sx, sy in [(cx - 130, 40), (cx + 130, 40), (cx + 80, cy - 80)]:
        _draw_shine(draw, sx, sy, 8, GOLD_LIGHT)

    font_l = _load_font(20)
    font_s = _load_font(13)
    _draw_label(draw, name, f"{material}  •  Fine Jewellery", W, H, font_l, font_s)
    img.convert("RGB").save(path, "WEBP", quality=88)


def _make_anklet(path, name="Silver Anklet", material="Silver"):
    W, H = 480, 380
    img = Image.new("RGBA", (W, H), BG + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    ac = {"gold": GOLD, "rose gold": ROSE_GOLD, "platinum": PLATINUM}.get(material.lower(), SILVER)
    lc = tuple(min(255, v + 60) for v in ac)
    cx, cy = W // 2, H // 2

    # Anklet oval
    Rx, Ry = 140, 55
    draw.ellipse([cx - Rx, cy - Ry, cx + Rx, cy + Ry], fill=None, outline=ac, width=4)
    # Chain links
    for angle in range(0, 361, 10):
        rad = math.radians(angle)
        x = cx + math.cos(rad) * Rx
        y = cy + math.sin(rad) * Ry
        draw.ellipse([x - 5, y - 4, x + 5, y + 4], fill=ac, outline=lc, width=1)

    # Tiny dangling charms at the bottom
    for dx in [-60, -30, 0, 30, 60]:
        bx = cx + dx
        by = cy + Ry + 4
        draw.line([bx, by, bx, by + 24], fill=ac, width=2)
        draw.ellipse([bx - 6, by + 22, bx + 6, by + 34], fill=lc, outline=ac, width=1)

    for sx, sy in [(cx - 160, cy - 90), (cx + 160, cy - 90), (cx, cy - 100)]:
        _draw_shine(draw, sx, sy, 6, GOLD_LIGHT)

    font_l = _load_font(20)
    font_s = _load_font(13)
    _draw_label(draw, name, f"{material}  •  Fine Jewellery", W, H, font_l, font_s)
    img.convert("RGB").save(path, "WEBP", quality=88)


def _make_nose_pin(path, name="Gold Nose Pin", material="Gold"):
    W, H = 480, 380
    img = Image.new("RGBA", (W, H), BG + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    nc = {"silver": SILVER, "platinum": PLATINUM}.get(material.lower(), GOLD)
    lc = tuple(min(255, v + 60) for v in nc)
    cx, cy = W // 2, H // 2

    # Nose pin wire curve
    for t in range(0, 181, 3):
        rad = math.radians(t)
        x = cx + math.cos(rad) * 45
        y = cy + 30 + math.sin(rad) * 25
        draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=nc)

    # Gem at top
    _draw_diamond_gem(draw, cx, cy, size=36)
    # Halo
    for angle in range(0, 360, 30):
        rad = math.radians(angle)
        draw.ellipse([cx + math.cos(rad)*26 - 5, cy + math.sin(rad)*26 - 5,
                      cx + math.cos(rad)*26 + 5, cy + math.sin(rad)*26 + 5],
                     fill=lc, outline=nc, width=1)

    for sx, sy in [(cx - 110, cy - 80), (cx + 110, cy - 80)]:
        _draw_shine(draw, sx, sy, 7, GOLD_LIGHT)

    font_l = _load_font(20)
    font_s = _load_font(13)
    _draw_label(draw, name, f"{material}  •  Fine Jewellery", W, H, font_l, font_s)
    img.convert("RGB").save(path, "WEBP", quality=88)


# ── Category-to-generator dispatch ──────────────────────────────────────────

CATEGORY_DIR_MAP = {
    "ring":     "rings",
    "necklace": "necklaces",
    "bracelet": "bracelets",
    "bangles":  "bangles",
    "earrings": "earrings",
    "pendant":  "pendants",
    "anklet":   "anklets",
    "chain":    "chains",
    "other":    "others",
}

# Maps DB category value → generator function
CATEGORY_GENERATORS = {
    "Ring":      _make_ring,
    "Necklace":  _make_necklace,
    "Bracelet":  _make_bracelet,
    "Bangles":   _make_bracelet,   # similar shape
    "Earrings":  _make_earrings,
    "Pendant":   _make_pendant,
    "Anklet":    _make_anklet,
    "Chain":     _make_necklace,   # similar style
    "Other":     _make_nose_pin,
}


def ensure_jewelry_library(base_dir: str):
    """
    Create static/images/jewelry/<category>/ directories and generate
    default category fallback images for each category.
    Returns dict: { 'Ring': 'images/jewelry/rings/default_ring.webp', ... }
    """
    lib_dir = os.path.join(base_dir, "static", "images", "jewelry")
    os.makedirs(lib_dir, exist_ok=True)

    defaults = {}
    for cat, subdir in CATEGORY_DIR_MAP.items():
        cat_dir = os.path.join(lib_dir, subdir)
        os.makedirs(cat_dir, exist_ok=True)
        fname = f"default_{subdir[:-1] if subdir.endswith('s') else subdir}.webp"
        fpath = os.path.join(cat_dir, fname)
        rel   = f"images/jewelry/{subdir}/{fname}"

        db_cat = cat.title()
        if not os.path.exists(fpath) and HAS_PIL:
            gen = CATEGORY_GENERATORS.get(db_cat, _make_nose_pin)
            try:
                gen(fpath, name=f"Premium {db_cat}", material="Gold")
                print(f"  [OK] Generated library image: {rel}")
            except Exception as e:
                print(f"  [FAIL] Failed to generate {rel}: {e}")

        defaults[db_cat] = rel

    return defaults


def generate_product_image(base_dir: str, item_id: int, name: str, category: str,
                           material: str, image_url: str) -> str:
    """
    Copy a category-specific premium jewellery image to uploads/products/ for this item
    instead of using PIL vector drawing.
    """
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name.lower())
    fname = f"{safe_name}.webp"
    rel   = f"uploads/products/{fname}"
    fpath = os.path.join(base_dir, "static", rel)

    if os.path.exists(fpath) and os.path.getsize(fpath) > 1000:
        return rel  # already exists, keep it

    os.makedirs(os.path.dirname(fpath), exist_ok=True)
    
    # Resolve fallback premium image using our priority helper function logic
    from utils.image_helpers import get_jewellery_image_path
    dummy_item = {'category': category, 'name': name}
    fallback_rel = get_jewellery_image_path(dummy_item)
    fallback_fpath = os.path.join(base_dir, "static", fallback_rel.replace('/', os.sep))
    
    if os.path.exists(fallback_fpath):
        import shutil
        try:
            shutil.copy2(fallback_fpath, fpath)
            print(f"  [OK] Assigned premium photo fallback to product image: {rel}")
        except Exception as e:
            print(f"  [FAIL] Failed to copy premium photo fallback: {e}")
    else:
        print(f"  [WARN] Fallback photo not found on disk: {fallback_fpath}")
        
    return rel


def assign_images_to_all_products(app):
    """
    Main entry point.
    - Ensures the category library exists.
    - For every product in jewellery_items:
        * If image_url points to a real file (> 5KB) -> keep it
        * Otherwise -> generate a product-specific image and update DB
    - Prints a verification table.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ensure_jewelry_library(base_dir)

    db_path = app.config["DATABASE_PATH"]
    conn    = sqlite3.connect(db_path)
    cur     = conn.cursor()

    rows = cur.execute(
        "SELECT item_id, name, category, material, image_url FROM jewellery_items"
    ).fetchall()

    print("\n" + "="*75)
    print("  {:<32} {:<12} {:<20} {:>5}".format('Product Name', 'Category', 'Assigned Image', 'OK?'))
    print("="*75)

    for item_id, name, category, material, image_url in rows:
        static_root = os.path.join(base_dir, "static")
        full_path   = os.path.join(static_root, image_url) if image_url else ""
        exists_ok   = bool(image_url and os.path.exists(full_path)
                           and os.path.getsize(full_path) > 1000)

        if not exists_ok:
            new_url = generate_product_image(
                base_dir, item_id, name, category, material, image_url or ""
            )
            cur.execute(
                "UPDATE jewellery_items SET image_url=?, image_path=? WHERE item_id=?",
                (new_url, new_url, item_id)
            )
            image_url = new_url
            full_path = os.path.join(static_root, image_url)
            exists_ok = os.path.exists(full_path) and os.path.getsize(full_path) > 1000

        short_img = image_url.split("/")[-1][:20] if image_url else "-"
        status    = "[YES]" if exists_ok else "[NO] "
        print("  {:<32} {:<12} {:<20} {:>5}".format(name[:32], category, short_img, status))

    conn.commit()
    conn.close()
    print("="*75)
    print("  [DONE] Image assignment complete.\n")


def get_product_image_url(item, static_root: str, defaults: dict) -> str:
    """
    Helper used in routes/templates.
    Returns the best available image_url for a product item.
    Priority: uploaded image > generated product image > category default.
    """
    if item.image_url:
        full = os.path.join(static_root, item.image_url)
        if os.path.exists(full) and os.path.getsize(full) > 1000:
            return item.image_url

    cat = getattr(item, "category", "Other")
    return defaults.get(cat, defaults.get("Other", "img/placeholder.png"))
