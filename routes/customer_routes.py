"""
Customer Routes — CRUD, purchase history, loyalty points, feedback
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required
import os

customer_bp = Blueprint('customer', __name__, url_prefix='/customers')


# ── List customers ────────────────────────────────────────────────────────────
@customer_bp.route('/')
@login_required
def list_customers():
    from database.models import get_all_customers
    search = request.args.get('q', '').strip()
    sort   = request.args.get('sort', 'name')
    customers = get_all_customers(search=search, sort_by=sort)
    return render_template('customers/list.html', customers=customers,
                           search=search, sort=sort)


# ── Add customer ──────────────────────────────────────────────────────────────
@customer_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        data = {
            'name':       request.form.get('name', '').strip(),
            'phone':      request.form.get('phone', '').strip(),
            'email':      request.form.get('email', '').strip(),
            'address':    request.form.get('address', '').strip(),
            'dob':        request.form.get('dob', ''),
            'anniversary':request.form.get('anniversary', ''),
            'gst_number': request.form.get('gst_number', '').strip(),
            'preferences':request.form.get('preferences', '').strip(),
        }
        if not data['name']:
            flash('Customer name is required.', 'warning')
        elif not data['phone']:
            flash('Phone number is required.', 'warning')
        else:
            try:
                from database.models import add_customer
                cid = add_customer(data)
                flash(f'Customer "{data["name"]}" added successfully!', 'success')
                return redirect(url_for('customer.customer_profile', customer_id=cid))
            except Exception as e:
                flash(f'Error adding customer: {str(e)}', 'danger')

    return render_template('customers/add.html')


# ── Customer Profile ──────────────────────────────────────────────────────────
@customer_bp.route('/profile/<int:customer_id>')
@login_required
def customer_profile(customer_id):
    from database.models import (get_customer_by_id, get_customer_purchase_history,
                        get_customer_feedback, get_customer_total_spent)
    customer  = get_customer_by_id(customer_id)
    if not customer:
        flash('Customer not found.', 'danger')
        return redirect(url_for('customer.list_customers'))
    history   = get_customer_purchase_history(customer_id)
    feedback  = get_customer_feedback(customer_id)
    total     = get_customer_total_spent(customer_id)
    return render_template('customers/profile.html', customer=customer,
                           history=history, feedback=feedback, total=total)


# ── Edit customer ─────────────────────────────────────────────────────────────
@customer_bp.route('/edit/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    from database.models import get_customer_by_id, update_customer
    customer = get_customer_by_id(customer_id)
    if not customer:
        flash('Customer not found.', 'danger')
        return redirect(url_for('customer.list_customers'))

    if request.method == 'POST':
        data = {
            'name':       request.form.get('name', '').strip(),
            'phone':      request.form.get('phone', '').strip(),
            'email':      request.form.get('email', '').strip(),
            'address':    request.form.get('address', '').strip(),
            'dob':        request.form.get('dob', ''),
            'anniversary':request.form.get('anniversary', ''),
            'gst_number': request.form.get('gst_number', '').strip(),
            'preferences':request.form.get('preferences', '').strip(),
        }
        try:
            update_customer(customer_id, data)
            flash('Customer updated successfully!', 'success')
            return redirect(url_for('customer.customer_profile', customer_id=customer_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    return render_template('customers/edit.html', customer=customer)


# ── Delete customer ───────────────────────────────────────────────────────────
@customer_bp.route('/delete/<int:customer_id>', methods=['POST'])
@login_required
def delete_customer(customer_id):
    try:
        from database.models import delete_customer
        delete_customer(customer_id)
        flash('Customer deleted.', 'info')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('customer.list_customers'))


# ── Add feedback ──────────────────────────────────────────────────────────────
@customer_bp.route('/feedback', methods=['POST'])
@login_required
def add_feedback():
    data = {
        'customer_id': int(request.form.get('customer_id', 0)),
        'item_id':     int(request.form.get('item_id', 0)),
        'rating':      int(request.form.get('rating', 5)),
        'comment':     request.form.get('comment', '').strip(),
    }
    try:
        from database.models import add_customer_feedback
        add_customer_feedback(data)
        flash('Feedback recorded. Thank you!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('customer.customer_profile', customer_id=data['customer_id']))


# ── Loyalty points ────────────────────────────────────────────────────────────
@customer_bp.route('/loyalty/<int:customer_id>', methods=['POST'])
@login_required
def update_loyalty(customer_id):
    points = int(request.form.get('points', 0))
    reason = request.form.get('reason', '')
    try:
        from database.models import update_loyalty_points
        update_loyalty_points(customer_id, points, reason)
        flash(f'Loyalty points updated (+{points}).', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('customer.customer_profile', customer_id=customer_id))


# ── Export customers ──────────────────────────────────────────────────────────
@customer_bp.route('/export')
@login_required
def export_customers():
    try:
        from database.models import get_all_customers
        from modules.excel_export import export_customers_to_excel
        customers = get_all_customers()
        filepath  = export_customers_to_excel(customers)
        return send_file(filepath, as_attachment=True,
                         download_name='customers_export.xlsx',
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        flash(f'Export error: {str(e)}', 'danger')
        return redirect(url_for('customer.list_customers'))


# ── AJAX: quick search (for billing) ─────────────────────────────────────────
@customer_bp.route('/api/search')
@login_required
def api_search():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    from database.models import search_customers
    return jsonify(search_customers(q, limit=10))