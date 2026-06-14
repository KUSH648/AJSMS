"""
database/migrate_images.py
==========================
Migration script that:
  1. Reads all products from jewellery_items
  2. Generates slug-based image filenames (e.g. "gold_kada.jpg")
  3. Creates placeholder PNG images for each product
  4. Creates a generic placeholder image for fallback
  5. Updates database with correct image_url values
  6. Logs debugging info per product
"""

import os
import sys
import re
import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    logger.error("Pillow (PIL) is required. Run: pip install Pillow")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "jewellery_shop.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads", "products")
PLACEHOLDER_PATH = os.path.join(BASE_DIR, "static", "img", "placeholder.png")
IMG_WIDTH, IMG_HEIGHT = 400, 300


def slugify(name):
    """Convert product name to filename-friendly slug."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s-]+", "_", s)
    s = s.strip("_")
    return s


def create_placeholder_image(filepath, product_name, category):
    """Create a simple placeholder image with product name and category."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), color=(13, 13, 22))
    draw = ImageDraw.Draw(img)

    # Draw a gold border
    gold_color = (212, 175, 55)
    for i in range(3):
        draw.rectangle(
            [i, i, IMG_WIDTH - 1 - i, IMG_HEIGHT - 1 - i],
            outline=gold_color,
        )

    # Try to load a font
    font_large = None
    font_small = None
    try:
        font_large = ImageFont.truetype("arial.ttf", 24)
        font_small = ImageFont.truetype("arial.ttf", 14)
    except (IOError, OSError):
        try:
            font_large = ImageFont.load_default()
            font_small = font_large
        except Exception:
            pass

    # Draw category icon area
    draw.ellipse(
        [(IMG_WIDTH // 2 - 30, 40), (IMG_WIDTH // 2 + 30, 100)],
        outline=gold_color,
        width=2,
    )

    # Draw product name centered
    if font_large:
        bbox = draw.textbbox((0, 0), product_name, font=font_large)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (IMG_WIDTH - tw) // 2
        y = 130
        draw.text((x, y), product_name, fill=gold_color, font=font_large)

    # Draw category below
    if font_small:
        cat_text = f"[ {category} ]"
        bbox = draw.textbbox((0, 0), cat_text, font=font_small)
        tw = bbox[2] - bbox[0]
        x = (IMG_WIDTH - tw) // 2
        draw.text((x, 175), cat_text, fill=(150, 150, 150), font=font_small)

    # Draw diamond icon
    diamond_points = [
        (IMG_WIDTH // 2, 210),
        (IMG_WIDTH // 2 + 12, 225),
        (IMG_WIDTH // 2, 245),
        (IMG_WIDTH // 2 - 12, 225),
    ]
    draw.polygon(diamond_points, outline=gold_color, fill=None, width=2)

    img.save(filepath, "PNG")
    logger.info(f"  Created: {os.path.basename(filepath)}")


def create_generic_placeholder():
    """Create a generic jewellery placeholder image."""
    os.makedirs(os.path.dirname(PLACEHOLDER_PATH), exist_ok=True)

    # Only create if it doesn't exist
    if os.path.exists(PLACEHOLDER_PATH):
        return

    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), color=(13, 13, 22))
    draw = ImageDraw.Draw(img)

    gold_color = (212, 175, 55)
    for i in range(3):
        draw.rectangle(
            [i, i, IMG_WIDTH - 1 - i, IMG_HEIGHT - 1 - i],
            outline=gold_color,
        )

    font = None
    try:
        font = ImageFont.truetype("arial.ttf", 22)
    except (IOError, OSError):
        font = ImageFont.load_default()

    # Draw a jewellery icon (simple gem shape)
    gem_pts = [
        (IMG_WIDTH // 2, 60),
        (IMG_WIDTH // 2 + 40, 100),
        (IMG_WIDTH // 2 + 25, 150),
        (IMG_WIDTH // 2 - 25, 150),
        (IMG_WIDTH // 2 - 40, 100),
    ]
    draw.polygon(gem_pts, outline=gold_color, width=3)

    text = "Jewellery Image"
    if font:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((IMG_WIDTH - tw) // 2, 175), text, fill=gold_color, font=font)

    sub_text = "Coming Soon"
    if font:
        bbox = draw.textbbox((0, 0), sub_text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((IMG_WIDTH - tw) // 2, 210), sub_text, fill=(150, 150, 150), font=font)

    img.save(PLACEHOLDER_PATH, "PNG")
    logger.info(f"  Created generic placeholder: {PLACEHOLDER_PATH}")


def main():
    logger.info("=" * 60)
    logger.info("IMAGE MIGRATION SCRIPT")
    logger.info("=" * 60)

    if not os.path.exists(DB_PATH):
        logger.error(f"Database not found: {DB_PATH}")
        sys.exit(1)

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Ensure image_url column exists
    cur.execute("PRAGMA table_info(jewellery_items)")
    columns = [row[1] for row in cur.fetchall()]
    if "image_url" not in columns:
        logger.info("Adding image_url column...")
        cur.execute("ALTER TABLE jewellery_items ADD COLUMN image_url TEXT")
        conn.commit()

    # Fetch all products
    products = cur.execute(
        "SELECT item_id, name, category, image_url, image_path FROM jewellery_items ORDER BY item_id"
    ).fetchall()

    if not products:
        logger.warning("No products found in database.")
        conn.close()
        return

    logger.info(f"Found {len(products)} products to process.")

    # Create generic placeholder first
    create_generic_placeholder()

    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    updated_count = 0
    for product in products:
        item_id = product["item_id"]
        name = product["name"]
        category = product["category"]
        old_image_url = product["image_url"]

        # Generate slug and image filename
        slug = slugify(name)
        if not slug:
            slug = f"product_{item_id}"
        filename = f"{slug}.png"
        web_path = f"uploads/products/{filename}"
        full_path = os.path.join(UPLOAD_DIR, filename)

        # Create placeholder image for this product
        create_placeholder_image(full_path, name, category)

        # Debug info
        logger.info(f"  Debug: Name='{name}' -> slug='{slug}' -> file='{filename}'")
        logger.info(f"  Debug: Image Exists={os.path.exists(full_path)}")

        # Update database
        cur.execute(
            "UPDATE jewellery_items SET image_url=?, image_path=? WHERE item_id=?",
            (web_path, web_path, item_id),
        )
        updated_count += 1

        # Log the change
        logger.info(f"  ID={item_id}: {old_image_url[:40] if old_image_url else 'None'} -> {web_path}")

    conn.commit()

    # Verify the updates
    logger.info("")
    logger.info("=" * 60)
    logger.info("VERIFICATION - All products after migration:")
    logger.info("=" * 60)
    verify = cur.execute(
        "SELECT item_id, name, image_url FROM jewellery_items ORDER BY item_id"
    ).fetchall()
    for v in verify:
        img_exists = os.path.exists(
            os.path.join(BASE_DIR, "static", v["image_url"]) if v["image_url"] else ""
        ) if v["image_url"] else False
        logger.info(
            f"  ID={v['item_id']:2d} | {v['name']:30s} | Image: {v['image_url']} | Exists: {img_exists}"
        )

    conn.close()
    logger.info("")
    logger.info(f"Migration complete. {updated_count} products updated.")
    logger.info(f"Images stored in: {UPLOAD_DIR}")


if __name__ == "__main__":
    main()
