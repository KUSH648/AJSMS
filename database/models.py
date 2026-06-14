"""
database/models.py
==================
Thin data-access helpers that wrap raw sqlite3 calls.
Every function takes an `app` or `db_path` and returns plain dicts / lists.
"""

import sqlite3
from flask import g, current_app
from datetime import datetime, date, timedelta
import calendar


# ─── Connection helper ──────────────────────────────────────────────────────


def get_db():
    """Return the per-request SQLite connection (stored in Flask's g)."""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE_PATH'],
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def query(sql, args=(), one=False):
    """Execute a SELECT and return Row(s) as dicts."""
    cur = get_db().execute(sql, args)
    rv = cur.fetchall()
    return (dict(rv[0]) if rv else None) if one else [dict(r) for r in rv]


def execute(sql, args=()):
    """Execute INSERT / UPDATE / DELETE, commit, return lastrowid."""
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur.lastrowid


# ═══════════════════════════════════════════════════════════════════════════
#  Jewellery Items
# ═══════════════════════════════════════════════════════════════════════════


def get_all_items(active_only=True):
    cond = "WHERE is_active = 1" if active_only else ""
    return query(f"SELECT * FROM jewellery_items {cond} ORDER BY category, name")


def get_item_by_id(item_id):
    return query("SELECT * FROM jewellery_items WHERE item_id = ?",
                 (item_id,), one=True)


def get_item_by_barcode(barcode):
    return query("SELECT * FROM jewellery_items WHERE barcode = ?",
                 (barcode,), one=True)


def search_items(term):
    t = f"%{term}%"
    return query("""
        SELECT * FROM jewellery_items
        WHERE (name LIKE ? OR category LIKE ? OR material LIKE ? OR barcode LIKE ?)
          AND is_active = 1
        ORDER BY name
    """, (t, t, t, t))


def get_low_stock_items(threshold=3):
    return query("""
        SELECT * FROM jewellery_items
        WHERE stock_qty <= ? AND is_active = 1
        ORDER BY stock_qty
    """, (threshold,))


def add_item(data):
    return execute("""
        INSERT INTO jewellery_items
          (name, category, material, purity, weight_gm, making_charges,
           cost_price, selling_price, stock_qty, barcode, image_path, image_url, description)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (data['name'], data['category'], data['material'], data['purity'],
          data['weight_gm'], data['making_charges'], data['cost_price'],
          data['selling_price'], data['stock_qty'], data.get('barcode'),
          data.get('image_path'), data.get('image_url'), data.get('description')))


def update_item(item_id, data):
    execute("""
        UPDATE jewellery_items
        SET name=?, category=?, material=?, purity=?, weight_gm=?,
            making_charges=?, cost_price=?, selling_price=?,
            stock_qty=?, barcode=?, description=?, image_path=?, image_url=?
        WHERE item_id=?
    """, (data['name'], data['category'], data['material'], data['purity'],
          data['weight_gm'], data['making_charges'], data['cost_price'],
          data['selling_price'], data['stock_qty'], data.get('barcode'),
          data.get('description'), data.get('image_path') or data.get('image_url'), data.get('image_url'), item_id))


def delete_item(item_id):
    execute("UPDATE jewellery_items SET is_active=0 WHERE item_id=?", (item_id,))


def update_stock(item_id, delta):
    execute("UPDATE jewellery_items SET stock_qty = stock_qty + ? WHERE item_id=?",
            (delta, item_id))


# ── Inventory-specific helpers (referenced by inventory_routes.py) ──────────


def get_all_inventory_items(search='', category='', material='', sort_by='name'):
    """Full filtered inventory list with search, category, material, and sort."""
    conditions = ["is_active = 1"]
    args = []

    if search:
        conditions.append("(name LIKE ? OR barcode LIKE ?)")
        t = f"%{search}%"
        args.extend([t, t])

    if category:
        conditions.append("category = ?")
        args.append(category)

    if material:
        conditions.append("material = ?")
        args.append(material)

    where = "WHERE " + " AND ".join(conditions)

    sort_map = {
        'name':     'name ASC',
        'price':    'selling_price DESC',
        'stock':    'stock_qty ASC',
        'category': 'category ASC, name ASC',
    }
    order = sort_map.get(sort_by, 'name ASC')

    return query(f"SELECT * FROM jewellery_items {where} ORDER BY {order}", args)


def search_inventory_items(q, limit=10):
    """Return items matching q (name/barcode) — lightweight dicts for AJAX."""
    t = f"%{q}%"
    return query("""
        SELECT item_id, name, category, selling_price, stock_qty, barcode
        FROM jewellery_items
        WHERE (name LIKE ? OR barcode LIKE ?) AND is_active = 1
        ORDER BY name
        LIMIT ?
    """, (t, t, limit))


def add_inventory_item(data):
    """Insert a new jewellery item. `data` uses 'price' for selling_price."""
    return execute("""
        INSERT INTO jewellery_items
          (name, category, material, weight_gm, purity,
           selling_price, cost_price, stock_qty, description,
           supplier, image_path, image_url)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (data['name'], data.get('category', ''), data.get('material', ''),
          data.get('weight_gm', 0), data.get('purity', ''),
          data.get('price', 0), data.get('cost_price', 0),
          data.get('stock_qty', 0), data.get('description', ''),
          data.get('supplier', ''), data.get('image_path'), data.get('image_url')))


def update_inventory_item(item_id, data):
    """Update a jewellery item. `data` uses 'price' for selling_price."""
    fields = ['name=?, category=?, material=?, weight_gm=?, purity=?',
              'selling_price=?, cost_price=?, stock_qty=?, description=?, supplier=?']
    args = [data['name'], data.get('category', ''), data.get('material', ''),
            data.get('weight_gm', 0), data.get('purity', ''),
            data.get('price', 0), data.get('cost_price', 0),
            data.get('stock_qty', 0), data.get('description', ''),
            data.get('supplier', '')]
    if 'image_path' in data:
        fields.append('image_path=?')
        args.append(data['image_path'])
    if 'image_url' in data:
        fields.append('image_url=?')
        args.append(data['image_url'])
    if 'barcode_image' in data:
        fields.append('barcode_image=?')
        args.append(data['barcode_image'])
    args.append(item_id)
    execute(f"UPDATE jewellery_items SET {', '.join(fields)} WHERE item_id=?", args)


def delete_inventory_item(item_id):
    """Soft-delete: set is_active=0."""
    execute("UPDATE jewellery_items SET is_active=0 WHERE item_id=?", (item_id,))


def get_item_sales_history(item_id):
    """Return sales history for a specific item from sale_items join sales."""
    return query("""
        SELECT s.sale_id, s.sale_date, s.total_amount, s.payment_method,
               c.name AS customer_name,
               si.quantity, si.unit_price, si.total_price
        FROM sale_items si
        JOIN sales s ON si.sale_id = s.sale_id
        LEFT JOIN customers c ON s.customer_id = c.customer_id
        WHERE si.item_id = ?
        ORDER BY s.sale_date DESC
    """, (item_id,))


# ═══════════════════════════════════════════════════════════════════════════
#  Customers
# ═══════════════════════════════════════════════════════════════════════════


def get_all_customers(search='', sort_by='name'):
    """Return customers with optional search and sorting."""
    conditions = []
    args = []

    if search:
        conditions.append("(name LIKE ? OR phone LIKE ? OR email LIKE ?)")
        t = f"%{search}%"
        args.extend([t, t, t])

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    sort_map = {
        'name':           'name ASC',
        'loyalty_points': 'loyalty_points DESC',
        'created_at':     'created_at DESC',
    }
    order = sort_map.get(sort_by, 'name ASC')

    return query(f"SELECT * FROM customers {where} ORDER BY {order}", args)


def get_customer_by_id(cid):
    return query("SELECT * FROM customers WHERE customer_id=?", (cid,), one=True)


def search_customers(q, limit=10):
    """Return customers matching q — lightweight dicts for AJAX."""
    t = f"%{q}%"
    return query("""
        SELECT customer_id, name, phone, loyalty_points
        FROM customers
        WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
        ORDER BY name
        LIMIT ?
    """, (t, t, t, limit))


def add_customer(data):
    """Insert customer, return customer_id."""
    return execute("""
        INSERT INTO customers
          (name, phone, email, address, dob, anniversary, preferences)
        VALUES (?,?,?,?,?,?,?)
    """, (data['name'], data.get('phone'), data.get('email'),
          data.get('address'), data.get('dob'), data.get('anniversary'),
          data.get('preferences', '[]')))


def update_customer(cid, data):
    """Update customer with all fields including gst_number."""
    execute("""
        UPDATE customers
        SET name=?, phone=?, email=?, address=?, dob=?, anniversary=?, preferences=?
        WHERE customer_id=?
    """, (data['name'], data.get('phone'), data.get('email'),
          data.get('address'), data.get('dob'), data.get('anniversary'),
          data.get('preferences', '[]'), cid))


def delete_customer(customer_id):
    """Delete a customer record."""
    execute("DELETE FROM customers WHERE customer_id=?", (customer_id,))


def get_customer_purchase_history(cid):
    return query("""
        SELECT s.sale_id, s.sale_date, s.total_amount, s.payment_method,
               ji.name AS item_name, ji.category,
               si.quantity, si.unit_price
        FROM sales s
        JOIN sale_items si ON s.sale_id = si.sale_id
        JOIN jewellery_items ji ON si.item_id = ji.item_id
        WHERE s.customer_id = ?
        ORDER BY s.sale_date DESC
    """, (cid,))


def get_customer_feedback(customer_id):
    """Return feedback for a specific customer with item_name, rating, comment."""
    return query("""
        SELECT f.feedback_id, f.rating, f.comment, f.created_at,
               ji.name AS item_name
        FROM feedback f
        LEFT JOIN jewellery_items ji ON f.item_id = ji.item_id
        WHERE f.customer_id = ?
        ORDER BY f.created_at DESC
    """, (customer_id,))


def get_customer_total_spent(customer_id):
    """Return total spent and order count for this customer."""
    row = query("""
        SELECT COALESCE(SUM(total_amount), 0) AS total_spent,
               COUNT(*)                       AS orders_count
        FROM sales
        WHERE customer_id = ?
    """, (customer_id,), one=True)
    if row:
        return {'total_spent': row['total_spent'], 'orders_count': row['orders_count']}
    return {'total_spent': 0, 'orders_count': 0}


def add_customer_feedback(data):
    """Insert feedback. data keys: customer_id, item_id, rating, comment."""
    return execute("""
        INSERT INTO feedback (customer_id, item_id, rating, comment)
        VALUES (?,?,?,?)
    """, (data['customer_id'], data['item_id'],
          data.get('rating', 5), data.get('comment', '')))


def update_loyalty_points(customer_id, points, reason=''):
    """Add points to a customer's loyalty balance."""
    execute("""
        UPDATE customers
        SET loyalty_points = loyalty_points + ?
        WHERE customer_id = ?
    """, (points, customer_id))


# ═══════════════════════════════════════════════════════════════════════════
#  Sales
# ═══════════════════════════════════════════════════════════════════════════


def get_all_sales(limit=100):
    return query("""
        SELECT s.*, c.name AS customer_name, e.name AS employee_name
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.customer_id
        LEFT JOIN employees e ON s.employee_id = e.employee_id
        ORDER BY s.sale_date DESC
        LIMIT ?
    """, (limit,))


def get_sale_by_id(sale_id):
    return query("SELECT * FROM sales WHERE sale_id=?", (sale_id,), one=True)


def get_sale_items(sale_id):
    return query("""
        SELECT si.*, ji.name AS item_name, ji.category, ji.material
        FROM sale_items si
        JOIN jewellery_items ji ON si.item_id = ji.item_id
        WHERE si.sale_id = ?
    """, (sale_id,))


def create_sale(data):
    sale_id = execute("""
        INSERT INTO sales
          (customer_id, employee_id, sale_date, subtotal, discount,
           gst_amount, total_amount, payment_method, notes, status)
        VALUES (?,?,datetime('now'),?,?,?,?,?,?,?)
    """, (data['customer_id'], data['employee_id'],
          data['subtotal'], data['discount'],
          data['gst_amount'], data['total_amount'],
          data['payment_method'], data.get('notes', ''), 'Completed'))
    return sale_id


def add_sale_item(sale_id, item_id, qty, unit_price):
    execute("""
        INSERT INTO sale_items (sale_id, item_id, quantity, unit_price, total_price)
        VALUES (?,?,?,?,?)
    """, (sale_id, item_id, qty, unit_price, round(unit_price * qty, 2)))


# ── Sales reporting helpers (referenced by sales_routes.py) ─────────────────


def get_daily_sales(date_str):
    """Return summary dict with total, count, gst, discount for a specific date."""
    row = query("""
        SELECT COALESCE(SUM(total_amount), 0)  AS total,
               COUNT(*)                        AS count,
               COALESCE(SUM(gst_amount), 0)    AS gst,
               COALESCE(SUM(discount), 0)      AS discount
        FROM sales
        WHERE date(sale_date) = ?
    """, (date_str,), one=True)
    return row if row else {'total': 0, 'count': 0, 'gst': 0, 'discount': 0}


def get_sales_by_date(date_str):
    """Return individual sale records for a date with customer_name, employee_name."""
    return query("""
        SELECT s.*, c.name AS customer_name, e.name AS employee_name
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.customer_id
        LEFT JOIN employees e ON s.employee_id = e.employee_id
        WHERE date(s.sale_date) = ?
        ORDER BY s.sale_date DESC
    """, (date_str,))


def get_monthly_sales(month, year):
    """Return daily breakdown (day, total, count) for a given month."""
    month_str = f"{year}-{month:02d}"
    return query("""
        SELECT CAST(strftime('%d', sale_date) AS INTEGER) AS day,
               COALESCE(SUM(total_amount), 0)             AS total,
               COUNT(*)                                    AS count
        FROM sales
        WHERE strftime('%Y-%m', sale_date) = ?
        GROUP BY day
        ORDER BY day
    """, (month_str,))


def get_monthly_summary(month, year):
    """Return aggregate dict (total_revenue, total_orders, total_gst, total_discount)."""
    month_str = f"{year}-{month:02d}"
    row = query("""
        SELECT COALESCE(SUM(total_amount), 0) AS total_revenue,
               COUNT(*)                       AS total_orders,
               COALESCE(SUM(gst_amount), 0)   AS total_gst,
               COALESCE(SUM(discount), 0)     AS total_discount
        FROM sales
        WHERE strftime('%Y-%m', sale_date) = ?
    """, (month_str,), one=True)
    return row if row else {
        'total_revenue': 0, 'total_orders': 0,
        'total_gst': 0, 'total_discount': 0
    }


def get_yearly_sales(year):
    """Return monthly totals with month_name, total, count for a year."""
    rows = query("""
        SELECT strftime('%m', sale_date)      AS month_num,
               COALESCE(SUM(total_amount), 0) AS total,
               COUNT(*)                       AS count
        FROM sales
        WHERE strftime('%Y', sale_date) = ?
        GROUP BY month_num
        ORDER BY month_num
    """, (str(year),))

    month_names = {
        '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
        '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
        '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec',
    }
    for r in rows:
        r['month_name'] = month_names.get(r['month_num'], r['month_num'])

    return rows


def get_all_sales_in_range(date_from, date_to):
    """Return all sales with customer_name, employee_name between dates."""
    return query("""
        SELECT s.*, c.name AS customer_name, e.name AS employee_name
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.customer_id
        LEFT JOIN employees e ON s.employee_id = e.employee_id
        WHERE date(s.sale_date) BETWEEN ? AND ?
        ORDER BY s.sale_date DESC
    """, (date_from, date_to))


def get_revenue_by_category():
    """Return category and revenue from sale_items join."""
    return query("""
        SELECT ji.category,
               COALESCE(SUM(si.total_price), 0) AS revenue
        FROM sale_items si
        JOIN jewellery_items ji ON si.item_id = ji.item_id
        GROUP BY ji.category
        ORDER BY revenue DESC
    """)


# ═══════════════════════════════════════════════════════════════════════════
#  Bills
# ═══════════════════════════════════════════════════════════════════════════


def get_all_bills(date_from='', date_to='', search='', limit=100):
    """Return bills with customer_name, customer_phone. Supports date range & search."""
    conditions = []
    args = []

    if date_from:
        conditions.append("date(b.bill_date) >= ?")
        args.append(date_from)

    if date_to:
        conditions.append("date(b.bill_date) <= ?")
        args.append(date_to)

    if search:
        conditions.append(
            "(b.bill_number LIKE ? OR c.name LIKE ? OR c.phone LIKE ?)"
        )
        t = f"%{search}%"
        args.extend([t, t, t])

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    return query(f"""
        SELECT b.*, c.name AS customer_name, c.phone AS customer_phone
        FROM bills b
        LEFT JOIN customers c ON b.customer_id = c.customer_id
        {where}
        ORDER BY b.bill_date DESC
        LIMIT ?
    """, args + [limit])


def get_bill_by_id(bill_id):
    """Enhanced: also returns customer_email, customer_address, payment_method."""
    return query("""
        SELECT b.*, c.name AS customer_name, c.phone AS customer_phone,
               c.email AS customer_email, c.address AS customer_address,
               s.payment_method
        FROM bills b
        LEFT JOIN customers c ON b.customer_id = c.customer_id
        LEFT JOIN sales s ON b.sale_id = s.sale_id
        WHERE b.bill_id = ?
    """, (bill_id,), one=True)


def get_bill_items(bill_id):
    """Return sale items for the sale associated with this bill."""
    return query("""
        SELECT si.*, ji.name AS item_name, ji.category, ji.material,
               ji.purity, ji.weight_gm
        FROM bills b
        JOIN sale_items si ON si.sale_id = b.sale_id
        JOIN jewellery_items ji ON si.item_id = ji.item_id
        WHERE b.bill_id = ?
    """, (bill_id,))


def get_bill_by_number(bill_no):
    return query("SELECT * FROM bills WHERE bill_number=?", (bill_no,), one=True)


def create_bill(data):
    return execute("""
        INSERT INTO bills
          (sale_id, customer_id, bill_number, bill_date, subtotal,
           cgst_amount, sgst_amount, gst_amount, discount, total_amount, status)
        VALUES (?,?,?,datetime('now'),?,?,?,?,?,?,?)
    """, (data['sale_id'], data['customer_id'], data['bill_number'],
          data['subtotal'], data['cgst_amount'], data['sgst_amount'],
          data['gst_amount'], data['discount'], data['total_amount'],
          data.get('status', 'Paid')))


def update_bill_paths(bill_id, pdf_path=None, qr_path=None):
    execute("UPDATE bills SET pdf_path=?, qr_code_path=? WHERE bill_id=?",
            (pdf_path, qr_path, bill_id))


def delete_bill(bill_id):
    """Delete a bill record."""
    execute("DELETE FROM bills WHERE bill_id=?", (bill_id,))


# ═══════════════════════════════════════════════════════════════════════════
#  Employees
# ═══════════════════════════════════════════════════════════════════════════


def get_all_employees(search='', role='', only_active=True, active_only=None):
    """Return employees with optional search and role filter.

    Accepts both `only_active` and legacy `active_only` kwargs for
    backwards compatibility.
    """
    # Support the legacy `active_only` kwarg used by existing callers
    if active_only is not None:
        only_active = active_only

    conditions = []
    args = []

    if only_active:
        conditions.append("is_active = 1")

    if search:
        conditions.append("(name LIKE ? OR phone LIKE ? OR email LIKE ?)")
        t = f"%{search}%"
        args.extend([t, t, t])

    if role:
        conditions.append("role = ?")
        args.append(role)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    return query(f"SELECT * FROM employees {where} ORDER BY role, name", args)


def get_employee_by_id(emp_id):
    return query("SELECT * FROM employees WHERE employee_id=?", (emp_id,), one=True)


def get_employee_by_email(email):
    return query("SELECT * FROM employees WHERE email=?", (email,), one=True)


def add_employee(data, password_hash):
    return execute("""
        INSERT INTO employees
          (name, phone, email, address, role, salary, join_date, password_hash)
        VALUES (?,?,?,?,?,?,?,?)
    """, (data['name'], data.get('phone'), data.get('email'),
          data.get('address'), data.get('role', 'Staff'),
          data.get('salary', 0), data.get('join_date'), password_hash))


def update_employee(emp_id, data):
    """Update employee – handles aadhar and pan fields too."""
    execute("""
        UPDATE employees
        SET name=?, phone=?, email=?, address=?, role=?, salary=?
        WHERE employee_id=?
    """, (data['name'], data.get('phone'), data.get('email'),
          data.get('address'), data.get('role', 'Staff'),
          data.get('salary', 0), emp_id))


def delete_employee(emp_id):
    """Soft-delete: set is_active=0."""
    execute("UPDATE employees SET is_active=0 WHERE employee_id=?", (emp_id,))


def deactivate_employee(emp_id):
    execute("UPDATE employees SET is_active=0 WHERE employee_id=?", (emp_id,))


# ═══════════════════════════════════════════════════════════════════════════
#  Attendance
# ═══════════════════════════════════════════════════════════════════════════


def mark_attendance(emp_id, work_date, check_in, check_out, status, notes=''):
    execute("""
        INSERT OR REPLACE INTO attendance
          (employee_id, work_date, check_in, check_out, status, notes)
        VALUES (?,?,?,?,?,?)
    """, (emp_id, work_date, check_in, check_out, status, notes))


def get_attendance(emp_id=None, month_year=None):
    cond, args = [], []
    if emp_id:
        cond.append("a.employee_id=?"); args.append(emp_id)
    if month_year:
        cond.append("strftime('%Y-%m', a.work_date)=?"); args.append(month_year)
    where = "WHERE " + " AND ".join(cond) if cond else ""
    return query(f"""
        SELECT a.*, e.name AS employee_name
        FROM attendance a
        JOIN employees e ON a.employee_id = e.employee_id
        {where}
        ORDER BY a.work_date DESC
    """, args)


def get_attendance_for_date(date_str):
    """Return dict mapping emp_id → status for a given date."""
    rows = query("""
        SELECT employee_id, status
        FROM attendance
        WHERE work_date = ?
    """, (date_str,))
    return {r['employee_id']: r['status'] for r in rows}


def save_attendance(date_str, records):
    """Save attendance. records is dict of {emp_id: status}.
    Insert or replace into attendance table for each employee."""
    for emp_id, status in records.items():
        check_in = None
        check_out = None
        if status.lower() in ('present', 'half-day', 'half'):
            check_in = '09:00'
        if status.lower() == 'present':
            check_out = '18:00'

        execute("""
            INSERT OR REPLACE INTO attendance
              (employee_id, work_date, check_in, check_out, status)
            VALUES (?,?,?,?,?)
        """, (int(emp_id), date_str, check_in, check_out, status))


def get_attendance_in_range(date_from, date_to):
    """Return attendance records between dates with employee_name."""
    return query("""
        SELECT a.*, e.name AS employee_name
        FROM attendance a
        JOIN employees e ON a.employee_id = e.employee_id
        WHERE a.work_date BETWEEN ? AND ?
        ORDER BY a.work_date DESC, e.name
    """, (date_from, date_to))


# ═══════════════════════════════════════════════════════════════════════════
#  Salary
# ═══════════════════════════════════════════════════════════════════════════


def add_salary_record(emp_id, month_year, base, bonus, deductions):
    net = base + bonus - deductions
    return execute("""
        INSERT OR REPLACE INTO salary_records
          (employee_id, month_year, base_salary, bonus, deductions, net_salary)
        VALUES (?,?,?,?,?,?)
    """, (emp_id, month_year, base, bonus, deductions, net))


def get_salary_records(emp_id=None):
    cond = "WHERE sr.employee_id=?" if emp_id else ""
    args = (emp_id,) if emp_id else ()
    return query(f"""
        SELECT sr.*, e.name AS employee_name
        FROM salary_records sr
        JOIN employees e ON sr.employee_id = e.employee_id
        {cond}
        ORDER BY sr.month_year DESC
    """, args)


def pay_salary(record_id):
    execute("UPDATE salary_records SET status='Paid', paid_on=? WHERE record_id=?",
            (datetime.now().strftime('%Y-%m-%d'), record_id))


# ═══════════════════════════════════════════════════════════════════════════
#  App Settings (key‑value store)
# ═══════════════════════════════════════════════════════════════════════════


def get_setting(key, default=None):
    row = query("SELECT value FROM app_settings WHERE key=?", (key,), one=True)
    return row['value'] if row else default


def set_setting(key, value):
    execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES (?,?)", (key, str(value)))


def get_all_settings():
    rows = query("SELECT key, value FROM app_settings ORDER BY key")
    return {r['key']: r['value'] for r in rows}


# ═══════════════════════════════════════════════════════════════════════════
#  Feedback
# ═══════════════════════════════════════════════════════════════════════════


def add_feedback(cid, item_id, rating, comment):
    return execute("""
        INSERT INTO feedback (customer_id, item_id, rating, comment)
        VALUES (?,?,?,?)
    """, (cid, item_id, rating, comment))


def get_all_feedback():
    return query("""
        SELECT f.*, c.name AS customer_name, ji.name AS item_name
        FROM feedback f
        LEFT JOIN customers c ON f.customer_id = c.customer_id
        LEFT JOIN jewellery_items ji ON f.item_id = ji.item_id
        ORDER BY f.created_at DESC
    """)


# ═══════════════════════════════════════════════════════════════════════════
#  Dashboard analytics
# ═══════════════════════════════════════════════════════════════════════════


def get_dashboard_stats():
    today = date.today().isoformat()
    month = today[:7]

    today_sales = query("""
        SELECT COALESCE(SUM(total_amount),0) AS total,
               COUNT(*) AS count
        FROM sales
        WHERE date(sale_date) = ?
    """, (today,), one=True)

    month_sales = query("""
        SELECT COALESCE(SUM(total_amount),0) AS total,
               COUNT(*) AS count
        FROM sales
        WHERE strftime('%Y-%m', sale_date) = ?
    """, (month,), one=True)

    total_items   = query("SELECT COUNT(*) AS n FROM jewellery_items WHERE is_active=1", one=True)
    total_cust    = query("SELECT COUNT(*) AS n FROM customers",                         one=True)
    low_stock     = query("SELECT COUNT(*) AS n FROM jewellery_items WHERE stock_qty<=3 AND is_active=1", one=True)
    total_emp     = query("SELECT COUNT(*) AS n FROM employees WHERE is_active=1",       one=True)

    return {
        'today_sales':       today_sales['total'],
        'today_orders':      today_sales['count'],
        'month_sales':       month_sales['total'],
        'month_orders':      month_sales['count'],
        'total_items':       total_items['n'],
        'total_customers':   total_cust['n'],
        'low_stock_count':   low_stock['n'],
        'total_employees':   total_emp['n'],
    }


def get_monthly_sales_chart(months=6):
    return query("""
        SELECT strftime('%Y-%m', sale_date) AS month,
               SUM(total_amount)            AS revenue,
               COUNT(*)                     AS orders
        FROM sales
        WHERE sale_date >= date('now', ?)
        GROUP BY month
        ORDER BY month
    """, (f'-{months} months',))


def get_category_sales():
    return query("""
        SELECT ji.category,
               SUM(si.total_price) AS revenue,
               SUM(si.quantity)    AS units
        FROM sale_items si
        JOIN jewellery_items ji ON si.item_id = ji.item_id
        GROUP BY ji.category
        ORDER BY revenue DESC
    """)


def get_top_items(limit=5):
    return query("""
        SELECT ji.item_id, ji.name, ji.category,
               SUM(si.quantity)    AS units_sold,
               SUM(si.total_price) AS revenue
        FROM sale_items si
        JOIN jewellery_items ji ON si.item_id = ji.item_id
        GROUP BY si.item_id
        ORDER BY revenue DESC
        LIMIT ?
    """, (limit,))


# ── Additional dashboard helpers (referenced by dashboard_routes.py) ────────


def get_recent_sales(limit=8):
    """Return recent sales with customer_name, employee_name, total_amount,
    sale_date, payment_method."""
    return query("""
        SELECT s.sale_id, s.sale_date, s.total_amount, s.payment_method,
               c.name AS customer_name, e.name AS employee_name
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.customer_id
        LEFT JOIN employees e ON s.employee_id = e.employee_id
        ORDER BY s.sale_date DESC
        LIMIT ?
    """, (limit,))


def get_monthly_revenue_chart():
    """Return dict with 'labels' (last 6 months as 'Jan','Feb'…) and 'values'
    (revenue per month)."""
    rows = query("""
        SELECT strftime('%Y-%m', sale_date) AS month,
               COALESCE(SUM(total_amount), 0) AS revenue
        FROM sales
        WHERE sale_date >= date('now', '-6 months')
        GROUP BY month
        ORDER BY month
    """)

    month_abbr = {
        '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
        '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
        '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec',
    }

    labels = []
    values = []
    for r in rows:
        mm = r['month'].split('-')[1] if '-' in r['month'] else r['month']
        labels.append(month_abbr.get(mm, mm))
        values.append(float(r['revenue']))

    return {'labels': labels, 'values': values}


def get_top_selling_items(limit=5):
    """Return items with name, category, units_sold, revenue from sale_items join."""
    return query("""
        SELECT ji.*,
               SUM(si.quantity)              AS units_sold,
               COALESCE(SUM(si.total_price), 0) AS revenue
        FROM sale_items si
        JOIN jewellery_items ji ON si.item_id = ji.item_id
        GROUP BY si.item_id
        ORDER BY units_sold DESC
        LIMIT ?
    """, (limit,))


def get_upcoming_birthdays(days=7):
    """Return customers whose birthday (dob) is in the next N days.
    Compares month-day only so it works across years."""
    today = date.today()
    results = []
    rows = query("""
        SELECT customer_id, name, phone, email, dob
        FROM customers
        WHERE dob IS NOT NULL AND dob != ''
    """)
    for r in rows:
        try:
            dob = datetime.strptime(r['dob'], '%Y-%m-%d').date()
            # Build this year's birthday
            this_year_bday = dob.replace(year=today.year)
            # If birthday already passed this year, check next year
            if this_year_bday < today:
                this_year_bday = dob.replace(year=today.year + 1)
            delta = (this_year_bday - today).days
            if 0 <= delta <= days:
                r['days_until'] = delta
                results.append(r)
        except (ValueError, TypeError):
            continue
    results.sort(key=lambda x: x['days_until'])
    return results


def get_daily_sales_range(start, end):
    """Return daily totals between two date strings with 'date' and 'total' keys."""
    return query("""
        SELECT date(sale_date) AS date,
               COALESCE(SUM(total_amount), 0) AS total
        FROM sales
        WHERE date(sale_date) BETWEEN ? AND ?
        GROUP BY date(sale_date)
        ORDER BY date(sale_date)
    """, (start, end))


def get_sales_by_category():
    """Return category and count from sale_items join grouped by category."""
    return query("""
        SELECT ji.category,
               COUNT(*) AS count
        FROM sale_items si
        JOIN jewellery_items ji ON si.item_id = ji.item_id
        GROUP BY ji.category
        ORDER BY count DESC
    """)
