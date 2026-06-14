"""
Billing Routes — new bill, GST calculation, PDF, QR, email, print, history
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from datetime import datetime
import json, os
from config import Config
from routes.auth_routes import role_required, admin_required

billing_bp = Blueprint('billing', __name__, url_prefix='/billing')

GST_RATE = 0.03   # 3% GST on jewellery (India)


# ── Bill history ──────────────────────────────────────────────────────────────
@billing_bp.route('/')
@login_required
def bill_history():
    from database.models import get_all_bills
    date_from = request.args.get('from', '')
    date_to   = request.args.get('to', '')
    search    = request.args.get('q', '').strip()
    bills     = get_all_bills(date_from=date_from, date_to=date_to, search=search)
    return render_template('billing/history.html', bills=bills,
                           date_from=date_from, date_to=date_to, search=search)


# ── New bill ──────────────────────────────────────────────────────────────────
@billing_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_bill():
    if request.method == 'POST':
        customer_id   = int(request.form.get('customer_id', 0) or 0)
        items_json    = request.form.get('items_json', '[]')
        payment_mode  = request.form.get('payment_mode', 'Cash')
        discount_pct  = float(request.form.get('discount_pct', 0) or 0)
        notes         = request.form.get('notes', '').strip()

        try:
            items = json.loads(items_json)
        except Exception:
            flash('Invalid item data.', 'danger')
            return redirect(url_for('billing.new_bill'))

        if not items:
            flash('Please add at least one item to the bill.', 'warning')
            return redirect(url_for('billing.new_bill'))

        # Build cart_items list expected by process_sale
        cart_items = []
        for it in items:
            cart_items.append({
                'item_id':  int(it.get('item_id') or it.get('id', 0)),
                'quantity': int(it.get('qty') or it.get('quantity', 1)),
            })

        # Calculate discount amount from percentage
        from database.models import get_item_by_id
        subtotal = 0.0
        for ci in cart_items:
            item = get_item_by_id(ci['item_id'])
            if item:
                subtotal += item['selling_price'] * ci['quantity']
        discount_amount = subtotal * discount_pct / 100.0

        try:
            from modules.billing import process_sale
            bill_id, bill_no, error = process_sale(
                customer_id=customer_id or None,
                employee_id=current_user.id,
                cart_items=cart_items,
                discount=discount_amount,
                payment_method=payment_mode,
                notes=notes,
            )
            if error:
                flash(f'Error creating bill: {error}', 'danger')
            else:
                flash(f'Bill #{bill_no} created successfully!', 'success')
                return redirect(url_for('billing.view_bill', bill_id=bill_id))
        except Exception as e:
            flash(f'Error creating bill: {str(e)}', 'danger')

    return render_template('billing/new_bill.html', gst_rate=GST_RATE * 100)


# ── View bill ─────────────────────────────────────────────────────────────────
@billing_bp.route('/view/<int:bill_id>')
@login_required
def view_bill(bill_id):
    from database.models import get_bill_by_id, get_bill_items
    bill  = get_bill_by_id(bill_id)
    if not bill:
        flash('Bill not found.', 'danger')
        return redirect(url_for('billing.bill_history'))
    items = get_bill_items(bill_id)

    # Generate QR code if not already present
    from modules.qr_generator import generate_bill_qr
    from modules.email_sender import is_mail_configured
    qr_path = generate_bill_qr(bill_id, bill)

    return render_template('billing/view_bill.html', bill=bill, items=items,
                           qr_path=qr_path, gst_rate=GST_RATE * 100,
                           smtp_configured=is_mail_configured())


# ── Generate / Download PDF ───────────────────────────────────────────────────
@billing_bp.route('/pdf/<int:bill_id>')
@login_required
def download_pdf(bill_id):
    from database.models import get_bill_by_id, get_bill_items
    from utils.pdf_generator import generate_invoice_pdf
    bill  = get_bill_by_id(bill_id)
    if not bill:
        flash('Bill not found.', 'danger')
        return redirect(url_for('billing.bill_history'))

    items = get_bill_items(bill_id)

    shop_cfg = {
        'name': Config.SHOP_NAME,
        'address': Config.SHOP_ADDRESS,
        'phone': Config.SHOP_PHONE,
        'email': Config.SHOP_EMAIL,
        'gstin': Config.SHOP_GSTIN,
        'pan': Config.SHOP_PAN
    }

    pdf_path = generate_invoice_pdf(bill, items, shop_cfg)
    return send_file(pdf_path, as_attachment=True,
                     download_name=f'invoice_{bill_id}.pdf',
                     mimetype='application/pdf')


# ── Email bill ────────────────────────────────────────────────────────────────
@billing_bp.route('/email/<int:bill_id>', methods=['POST'])
@login_required
def email_bill(bill_id):
    from database.models import get_bill_by_id, get_bill_items
    from utils.pdf_generator import generate_invoice_pdf
    from modules.email_sender import send_invoice_email, is_mail_configured

    bill  = get_bill_by_id(bill_id)
    if not bill:
        flash('Bill not found.', 'danger')
        return redirect(url_for('billing.bill_history'))

    to_email = request.form.get('email', '').strip() or bill.get('customer_email', '')
    if not to_email:
        flash('No email address provided or on file.', 'warning')
        return redirect(url_for('billing.view_bill', bill_id=bill_id))

    if not is_mail_configured():
        flash('SMTP email not configured. Go to <a href="' + url_for('settings.index') + '" class="text-warning">Settings</a> to set up email sending, then try again.', 'warning')
        return redirect(url_for('billing.view_bill', bill_id=bill_id))

    items = get_bill_items(bill_id)
    shop_cfg = {
        'name': Config.SHOP_NAME,
        'address': Config.SHOP_ADDRESS,
        'phone': Config.SHOP_PHONE,
        'email': Config.SHOP_EMAIL,
        'gstin': Config.SHOP_GSTIN,
        'pan': Config.SHOP_PAN,
    }

    try:
        pdf_path = generate_invoice_pdf(bill, items, shop_cfg)
        ok = send_invoice_email(to_email, bill, pdf_path)
        if ok:
            flash(f'Invoice emailed successfully to {to_email}!', 'success')
        else:
            flash(f'Failed to send email to {to_email}. Check <a href="' + url_for('settings.index') + '" class="text-warning">SMTP settings</a> or try again.', 'danger')
    except Exception as e:
        flash(f'Email error: {str(e)}', 'danger')
    return redirect(url_for('billing.view_bill', bill_id=bill_id))


# ── Delete bill (admin only) ──────────────────────────────────────────────────
@billing_bp.route('/delete/<int:bill_id>', methods=['POST'])
@admin_required
def delete_bill(bill_id):
    if getattr(current_user, 'role', '').lower() != 'admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('billing.bill_history'))

    try:
        from database.models import delete_bill
        delete_bill(bill_id)
        flash('Bill deleted.', 'info')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('billing.bill_history'))


# ── AJAX: calculate bill preview ──────────────────────────────────────────────
@billing_bp.route('/api/calculate', methods=['POST'])
@login_required
def api_calculate():
    data = request.get_json()
    items       = data.get('items', [])
    discount    = float(data.get('discount_pct', 0))
    gst_rate    = float(data.get('gst_rate', GST_RATE * 100)) / 100
    use_loyalty = data.get('use_loyalty', False)
    loyalty_pts = int(data.get('loyalty_points', 0))

    subtotal    = sum(float(i.get('price') or i.get('selling_price', 0)) * int(i.get('qty', 1)) for i in items)
    discount_amt= subtotal * discount / 100
    loyalty_dis = (loyalty_pts * 0.10) if use_loyalty else 0    # ₹0.10 per point
    after_disc  = subtotal - discount_amt - loyalty_dis
    gst_amount  = after_disc * gst_rate
    total       = after_disc + gst_amount

    return jsonify({
        'subtotal':     round(subtotal, 2),
        'discount_amt': round(discount_amt, 2),
        'loyalty_dis':  round(loyalty_dis, 2),
        'gst_amount':   round(gst_amount, 2),
        'total':        round(total, 2),
    })


# ── AJAX: submit bill from JS cart ───────────────────────────────────────────
@billing_bp.route('/api/submit', methods=['POST'])
@login_required
def api_submit():
    """Accept a JSON cart from the frontend and create a sale + bill."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data received'}), 400

    items       = data.get('items', [])
    customer_id = data.get('customer_id') or None
    payment     = data.get('payment_method', 'Cash')
    discount    = float(data.get('discount', 0))
    notes       = data.get('notes', '')

    if not items:
        return jsonify({'error': 'Cart is empty'}), 400

    # Build cart_items expected by process_sale
    cart_items = []
    for it in items:
        cart_items.append({
            'item_id':  int(it.get('item_id') or it.get('id', 0)),
            'quantity': int(it.get('qty') or it.get('quantity', 1)),
        })

    try:
        from modules.billing import process_sale
        bill_id, bill_no, error = process_sale(
            customer_id=int(customer_id) if customer_id else None,
            employee_id=current_user.id,
            cart_items=cart_items,
            discount=discount,
            payment_method=payment,
            notes=notes,
        )
        if error:
            return jsonify({'error': error}), 400

        return jsonify({
            'bill_id':   bill_id,
            'bill_no':   bill_no,
            'redirect':  url_for('billing.view_bill', bill_id=bill_id),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Export bills to Excel ─────────────────────────────────────────────────────
@billing_bp.route('/export')
@login_required
def export_bills():
    try:
        from database.models import get_all_bills
        from modules.excel_export import export_bills_to_excel
        bills    = get_all_bills()
        filepath = export_bills_to_excel(bills)
        return send_file(filepath, as_attachment=True, download_name='bills_export.xlsx',
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        flash(f'Export error: {str(e)}', 'danger')
        return redirect(url_for('billing.bill_history'))