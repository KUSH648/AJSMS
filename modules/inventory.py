"""
modules/inventory.py
====================
Business-logic layer for Jewellery Items / Inventory.
"""

import os
import uuid
from flask import current_app
from database.models import (
    get_all_items, get_item_by_id, get_item_by_barcode,
    search_items, get_low_stock_items,
    add_item, update_item, delete_item, update_stock, query
)
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
CATEGORIES = ['Ring', 'Necklace', 'Bracelet', 'Earrings', 'Anklet', 'Pendant',
              'Bangles', 'Brooch', 'Chain', 'Other']
MATERIALS  = ['Gold', 'Silver', 'Platinum', 'Rose Gold', 'White Gold']
PURITIES   = ['24K', '22K', '18K', '14K', '92.5', 'PT950', 'PT900']


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_item_image(file):
    """Save uploaded image; return relative path or None."""
    if not file or file.filename == '':
        return None
    if not allowed_file(file.filename):
        return None
    ext = file.filename.rsplit('.', 1)[1].lower()
    fname = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, fname))
    return f"uploads/{fname}"


def save_product_image(file):
    """Save uploaded product image in static/uploads/products/; return relative path uploads/products/{fname} or None."""
    if not file or file.filename == '':
        return None
    if not allowed_file(file.filename):
        return None
    ext = file.filename.rsplit('.', 1)[1].lower()
    fname = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'products')
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, fname))
    return f"uploads/products/{fname}"


def get_inventory_summary():
    """Return aggregate stats for the inventory."""
    items = get_all_items()
    total_value = sum(i['selling_price'] * i['stock_qty'] for i in items)
    by_category = {}
    for item in items:
        cat = item['category']
        by_category.setdefault(cat, {'count': 0, 'value': 0})
        by_category[cat]['count'] += 1
        by_category[cat]['value'] += item['selling_price'] * item['stock_qty']
    low = get_low_stock_items(current_app.config.get('LOW_STOCK_THRESHOLD', 3))
    return {
        'total_items':   len(items),
        'total_value':   round(total_value, 2),
        'low_stock':     low,
        'by_category':   by_category,
    }


def generate_barcode_id():
    """Generate a unique barcode string JW-XXXXXX."""
    existing = {r['barcode'] for r in query("SELECT barcode FROM jewellery_items WHERE barcode IS NOT NULL")}
    while True:
        code = f"JW-{uuid.uuid4().hex[:6].upper()}"
        if code not in existing:
            return code


def add_jewellery_item(form_data, image_file=None):
    """Validate and insert a new item; return (item_id, error)."""
    name = form_data.get('name', '').strip()
    if not name:
        return None, 'Item name is required.'

    try:
        selling_price = float(form_data.get('selling_price', 0))
        if selling_price <= 0:
            return None, 'Selling price must be > 0.'
        cost_price     = float(form_data.get('cost_price', 0))
        making_charges = float(form_data.get('making_charges', 0))
        weight_gm      = float(form_data.get('weight_gm', 0))
        stock_qty      = int(form_data.get('stock_qty', 0))
    except ValueError:
        return None, 'Invalid numeric values.'

    barcode = form_data.get('barcode', '').strip() or generate_barcode_id()
    if get_item_by_barcode(barcode):
        return None, f'Barcode "{barcode}" already exists.'

    image_path = save_item_image(image_file) if image_file else None

    data = {
        'name':           name,
        'category':       form_data.get('category', 'Other'),
        'material':       form_data.get('material', 'Gold'),
        'purity':         form_data.get('purity', '22K'),
        'weight_gm':      weight_gm,
        'making_charges': making_charges,
        'cost_price':     cost_price,
        'selling_price':  selling_price,
        'stock_qty':      stock_qty,
        'barcode':        barcode,
        'image_path':     image_path,
        'description':    form_data.get('description', ''),
    }
    item_id = add_item(data)
    return item_id, None


def update_jewellery_item(item_id, form_data):
    """Validate and update an existing item; return error or None."""
    name = form_data.get('name', '').strip()
    if not name:
        return 'Item name is required.'
    try:
        sp  = float(form_data.get('selling_price', 0))
        cp  = float(form_data.get('cost_price', 0))
        mc  = float(form_data.get('making_charges', 0))
        wt  = float(form_data.get('weight_gm', 0))
        qty = int(form_data.get('stock_qty', 0))
    except ValueError:
        return 'Invalid numeric values.'

    data = {
        'name':           name,
        'category':       form_data.get('category', 'Other'),
        'material':       form_data.get('material', 'Gold'),
        'purity':         form_data.get('purity', '22K'),
        'weight_gm':      wt,
        'making_charges': mc,
        'cost_price':     cp,
        'selling_price':  sp,
        'stock_qty':      qty,
        'barcode':        form_data.get('barcode', ''),
        'description':    form_data.get('description', ''),
    }
    update_item(item_id, data)
    return None


def get_barcode_image_path(item_id):
    """Return the filesystem path to an item's barcode PNG."""
    item = get_item_by_id(item_id)
    if not item or not item.get('barcode'):
        return None
    barcode_str = item['barcode']
    barcode_dir = os.path.join('static', 'barcodes')
    return os.path.join(barcode_dir, f"{barcode_str}.png")


def generate_barcode(item_id):
    """Generate a physical barcode PNG image for the item."""
    import barcode
    from barcode.writer import ImageWriter
    
    item = get_item_by_id(item_id)
    if not item or not item.get('barcode'):
        return None
    
    barcode_str = item['barcode']
    barcode_dir = os.path.join('static', 'barcodes')
    os.makedirs(barcode_dir, exist_ok=True)
    
    try:
        # Code128 is a standard readable barcode format
        code_class = barcode.get_barcode_class('code128')
        my_code = code_class(barcode_str, writer=ImageWriter())
        filename = os.path.join(barcode_dir, barcode_str)
        # my_code.save will automatically append '.png'
        my_code.save(filename)
        return os.path.join(barcode_dir, f"{barcode_str}.png")
    except Exception as e:
        print(f"Error generating barcode PNG for {barcode_str}: {e}")
        return None

