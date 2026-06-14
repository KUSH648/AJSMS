"""
Inventory Routes — CRUD for jewellery items, barcode, search, export
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required
from routes.auth_routes import admin_required
import os

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

CATEGORIES = ['Ring', 'Necklace', 'Bracelet', 'Earrings', 'Anklet', 'Pendant',
              'Bangles', 'Brooch', 'Chain', 'Other']
MATERIALS  = ['Gold', 'Silver', 'Platinum', 'Rose Gold', 'White Gold']

MATERIAL_PRICES = {
    'Gold':      6500,
    'Silver':    85,
    'Platinum':  3200,
    'Rose Gold': 5500,
    'White Gold': 6000,
}


def get_material_price(material, weight_gm=1.0, purity='22K'):
    """Calculate default selling price based on material, weight, and purity."""
    base = MATERIAL_PRICES.get(material, MATERIAL_PRICES['Gold'])
    purity_mult = {'24K': 1.0, '22K': 0.92, '18K': 0.75, '14K': 0.58,
                   '92.5': 0.012, 'PT950': 0.48, 'PT900': 0.45}
    mult = purity_mult.get(purity, 0.92)
    return round(base * weight_gm * mult, 2)


# ── List / Search ─────────────────────────────────────────────────────────────
@inventory_bp.route('/')
@login_required
def list_items():
    from database.models import get_all_inventory_items, get_low_stock_items
    search   = request.args.get('q', '').strip()
    category = request.args.get('category', '')
    material = request.args.get('material', '')
    sort_by  = request.args.get('sort', 'name')

    items = get_all_inventory_items(search=search, category=category,
                                    material=material, sort_by=sort_by)
    low_stock_ids = {i['item_id'] for i in get_low_stock_items(threshold=5)}

    return render_template(
        'inventory/list.html',
        items=items, search=search, category=category,
        material=material, sort_by=sort_by,
        categories=CATEGORIES, materials=MATERIALS,
        low_stock_ids=low_stock_ids
    )


# ── Add Item ──────────────────────────────────────────────────────────────────
@inventory_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        material = request.form.get('material', '')
        weight_gm = float(request.form.get('weight_gm', 0) or 0)
        purity = request.form.get('purity', '22K').strip()
        price = float(request.form.get('price', 0) or 0)
        if price <= 0 and material and weight_gm > 0:
            price = get_material_price(material, weight_gm, purity)
        data = {
            'name':        request.form.get('name', '').strip(),
            'category':    request.form.get('category', ''),
            'material':    material,
            'weight_gm':   weight_gm,
            'purity':      purity,
            'price':       price,
            'cost_price':  float(request.form.get('cost_price', 0) or 0),
            'stock_qty':   int(request.form.get('stock_qty', 0) or 0),
            'description': request.form.get('description', '').strip(),
            'supplier':    request.form.get('supplier', '').strip(),
        }
        if not data['name']:
            flash('Item name is required.', 'warning')
        elif data['price'] <= 0:
            flash('Price must be greater than zero.', 'warning')
        else:
            try:
                from database.models import add_inventory_item
                from modules.inventory import generate_barcode, save_product_image
                item_image = request.files.get('item_image')
                if item_image and item_image.filename:
                    img_url = save_product_image(item_image)
                    if img_url:
                        data['image_url'] = img_url
                        data['image_path'] = img_url
                item_id = add_inventory_item(data)
                generate_barcode(item_id)
                flash(f'"{data["name"]}" added to inventory!', 'success')
                return redirect(url_for('inventory.list_items'))
            except Exception as e:
                flash(f'Error adding item: {str(e)}', 'danger')

    return render_template('inventory/add.html', categories=CATEGORIES, materials=MATERIALS)


# ── Edit Item ─────────────────────────────────────────────────────────────────
@inventory_bp.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    from database.models import get_item_by_id, update_inventory_item
    item = get_item_by_id(item_id)
    if not item:
        flash('Item not found.', 'danger')
        return redirect(url_for('inventory.list_items'))

    if request.method == 'POST':
        material = request.form.get('material', '')
        weight_gm = float(request.form.get('weight_gm', 0) or 0)
        purity = request.form.get('purity', '22K').strip()
        price = float(request.form.get('price', 0) or 0)
        if price <= 0 and material and weight_gm > 0:
            price = get_material_price(material, weight_gm, purity)
        data = {
            'name':        request.form.get('name', '').strip(),
            'category':    request.form.get('category', ''),
            'material':    material,
            'weight_gm':   weight_gm,
            'purity':      purity,
            'price':       price,
            'cost_price':  float(request.form.get('cost_price', 0) or 0),
            'stock_qty':   int(request.form.get('stock_qty', 0) or 0),
            'description': request.form.get('description', '').strip(),
            'supplier':    request.form.get('supplier', '').strip(),
        }
        item_image = request.files.get('item_image')
        barcode_image = request.files.get('barcode_image')
        if item_image and item_image.filename:
            from modules.inventory import save_product_image
            img_url = save_product_image(item_image)
            if img_url:
                data['image_url'] = img_url
                data['image_path'] = img_url
        if barcode_image and barcode_image.filename:
            from modules.inventory import save_item_image
            barcode_path = save_item_image(barcode_image)
            if barcode_path:
                data['barcode_image'] = barcode_path
        try:
            update_inventory_item(item_id, data)
            flash('Item updated successfully!', 'success')
            return redirect(url_for('inventory.list_items'))
        except Exception as e:
            flash(f'Error updating item: {str(e)}', 'danger')

    return render_template('inventory/edit.html', item=item,
                           categories=CATEGORIES, materials=MATERIALS)


# ── Delete Item ───────────────────────────────────────────────────────────────
@inventory_bp.route('/delete/<int:item_id>', methods=['POST'])
@admin_required
def delete_item(item_id):
    try:
        from database.models import delete_inventory_item
        delete_inventory_item(item_id)
        flash('Item deleted from inventory.', 'info')
    except Exception as e:
        flash(f'Error deleting item: {str(e)}', 'danger')
    return redirect(url_for('inventory.list_items'))


# ── View single item ──────────────────────────────────────────────────────────
@inventory_bp.route('/view/<int:item_id>')
@login_required
def view_item(item_id):
    from database.models import get_item_by_id, get_item_sales_history
    item    = get_item_by_id(item_id)
    history = get_item_sales_history(item_id)
    if not item:
        flash('Item not found.', 'danger')
        return redirect(url_for('inventory.list_items'))
    return render_template('inventory/view.html', item=item, history=history)


# ── Barcode endpoint ──────────────────────────────────────────────────────────
@inventory_bp.route('/barcode/<int:item_id>')
@login_required
def get_barcode(item_id):
    from modules.inventory import get_barcode_image_path
    path = get_barcode_image_path(item_id)
    if path and os.path.exists(path):
        return send_file(path, mimetype='image/png')
    return jsonify({'error': 'Barcode not found'}), 404


# ── AJAX: scan barcode ────────────────────────────────────────────────────────
@inventory_bp.route('/api/scan-barcode', methods=['POST'])
@login_required
def scan_barcode():
    from modules.barcode_scanner import decode_barcode_from_base64
    image_b64 = request.json.get('image', '')
    barcode   = decode_barcode_from_base64(image_b64)
    if barcode:
        from database.models import get_item_by_barcode
        item = get_item_by_barcode(barcode)
        return jsonify({'barcode': barcode, 'item': item})
    return jsonify({'error': 'No barcode detected'}), 400


# ── Export inventory to Excel ─────────────────────────────────────────────────
@inventory_bp.route('/export')
@login_required
def export_inventory():
    try:
        from database.models import get_all_inventory_items
        from modules.excel_export import export_inventory_to_excel
        items    = get_all_inventory_items()
        filepath = export_inventory_to_excel(items)
        return send_file(filepath, as_attachment=True,
                         download_name='inventory_export.xlsx',
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        flash(f'Export error: {str(e)}', 'danger')
        return redirect(url_for('inventory.list_items'))


# ── AJAX: search items (for billing dropdown) ─────────────────────────────────
@inventory_bp.route('/api/search')
@login_required
def api_search():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    from database.models import search_inventory_items
    items = search_inventory_items(q, limit=10)
    return jsonify(items)