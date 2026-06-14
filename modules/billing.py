"""
modules/billing.py
==================
Invoice creation, GST calculation, and bill management.
"""

from flask import current_app
from datetime import datetime
from database.models import (
    create_sale, add_sale_item, create_bill, update_bill_paths,
    get_all_bills, get_bill_by_id, query, execute, get_item_by_id,
    update_stock
)


def calculate_gst(subtotal, discount=0.0):
    """Return dict with GST breakdown (India: 3% on jewellery)."""
    cfg = current_app.config
    gst_rate  = cfg.get('GST_RATE',  3.0)
    cgst_rate = cfg.get('CGST_RATE', 1.5)
    sgst_rate = cfg.get('SGST_RATE', 1.5)

    taxable    = max(0.0, subtotal - discount)
    gst_amount = round(taxable * gst_rate  / 100, 2)
    cgst       = round(taxable * cgst_rate / 100, 2)
    sgst       = round(taxable * sgst_rate / 100, 2)
    total      = round(taxable + gst_amount, 2)

    return {
        'subtotal':    round(subtotal,    2),
        'discount':    round(discount,    2),
        'taxable':     round(taxable,     2),
        'gst_rate':    gst_rate,
        'cgst_rate':   cgst_rate,
        'sgst_rate':   sgst_rate,
        'cgst_amount': cgst,
        'sgst_amount': sgst,
        'gst_amount':  gst_amount,
        'total':       total,
    }


def next_bill_number():
    """Generate the next sequential bill number (BILL-XXXXX)."""
    row = query("SELECT bill_number FROM bills ORDER BY bill_id DESC LIMIT 1", one=True)
    if row and row['bill_number']:
        try:
            seq = int(row['bill_number'].split('-')[1]) + 1
        except Exception:
            seq = 1001
    else:
        seq = 1001
    return f"BILL-{seq:05d}"


def process_sale(customer_id, employee_id, cart_items,
                 discount=0.0, payment_method='Cash', notes=''):
    """
    Create a Sale + SaleItems + Bill in one transaction.

    cart_items: list of {'item_id': int, 'quantity': int}
    Returns: (bill_id, bill_number, error_message)
    """
    if not cart_items:
        return None, None, 'Cart is empty.'

    subtotal = 0.0
    line_data = []
    for ci in cart_items:
        item = get_item_by_id(ci['item_id'])
        if not item:
            return None, None, f"Item ID {ci['item_id']} not found."
        qty = int(ci.get('quantity', 1))
        if item['stock_qty'] < qty:
            return None, None, f"Insufficient stock for {item['name']}."
        price = item['selling_price']
        subtotal += price * qty
        line_data.append({'item': item, 'qty': qty, 'price': price})

    gst_info = calculate_gst(subtotal, discount)

    sale_data = {
        'customer_id':    customer_id,
        'employee_id':    employee_id,
        'subtotal':       gst_info['subtotal'],
        'discount':       gst_info['discount'],
        'gst_amount':     gst_info['gst_amount'],
        'total_amount':   gst_info['total'],
        'payment_method': payment_method,
        'notes':          notes,
    }
    sale_id = create_sale(sale_data)

    for ld in line_data:
        add_sale_item(sale_id, ld['item']['item_id'], ld['qty'], ld['price'])
        update_stock(ld['item']['item_id'], -ld['qty'])

    bill_no = next_bill_number()
    bill_data = {
        'sale_id':     sale_id,
        'customer_id': customer_id,
        'bill_number': bill_no,
        'subtotal':    gst_info['subtotal'],
        'cgst_amount': gst_info['cgst_amount'],
        'sgst_amount': gst_info['sgst_amount'],
        'gst_amount':  gst_info['gst_amount'],
        'discount':    gst_info['discount'],
        'total_amount': gst_info['total'],
        'status':      'Paid',
    }
    bill_id = create_bill(bill_data)

    return bill_id, bill_no, None


def get_daily_collection(date_str=None):
    """Return total collection for a given date (default: today)."""
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    row = query("""
        SELECT COALESCE(SUM(total_amount), 0) AS total,
               COUNT(*) AS count
        FROM sales
        WHERE date(sale_date) = ?
    """, (date_str,), one=True)
    return row


def get_monthly_report(year, month):
    """Return daily breakdown for a given month."""
    m = f"{year}-{month:02d}"
    return query("""
        SELECT date(sale_date) AS day,
               SUM(total_amount)  AS revenue,
               SUM(gst_amount)    AS gst,
               SUM(discount)      AS discount,
               COUNT(*)           AS orders
        FROM sales
        WHERE strftime('%Y-%m', sale_date) = ?
        GROUP BY day
        ORDER BY day
    """, (m,))
