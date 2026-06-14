"""
database/db_setup.py
====================
Creates all SQLite tables and inserts demo seed data on first run.
"""

import sqlite3
import os
import re
import bcrypt
from datetime import datetime, date, timedelta
import random

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def _slugify(name):
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s-]+", "_", s)
    return s.strip("_")


def _create_placeholder_image(filepath, product_name, category, size=(400, 300)):
    """Assign a premium category-specific jewelry image instead of PIL drawing."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    if os.path.exists(filepath):
        return
    cat_lower = category.lower()
    name_lower = product_name.lower()
    fallback_rel = 'images/jewelry/others/default_other.webp'
    
    if cat_lower == 'ring':
        if 'solitaire' in name_lower or 'diamond' in name_lower or 'platinum' in name_lower:
            fallback_rel = 'images/jewelry/rings/platinum_ring.webp'
        else:
            fallback_rel = 'images/jewelry/rings/default_ring.webp'
    elif cat_lower == 'necklace':
        if 'royal' in name_lower or 'diamond' in name_lower:
            fallback_rel = 'images/jewelry/necklaces/royal_diamond_necklace.webp'
        else:
            fallback_rel = 'images/jewelry/necklaces/default_necklace.webp'
    elif cat_lower in ['bracelet', 'anklet', 'bangles']:
        if 'bangle' in name_lower:
            fallback_rel = 'images/jewelry/bangles/default_bangle.webp'
        elif 'kada' in name_lower or 'gold' in name_lower:
            fallback_rel = 'images/jewelry/bracelets/gold_kada.webp'
        elif 'diamond' in name_lower:
            fallback_rel = 'images/jewelry/bracelets/diamond_bracelet.webp'
        elif cat_lower == 'anklet' or 'anklet' in name_lower:
            fallback_rel = 'images/jewelry/anklets/default_anklet.webp'
        else:
            fallback_rel = 'images/jewelry/bracelets/default_bracelet.webp'
    elif cat_lower == 'earrings':
        if 'rose gold' in name_lower or 'diamond' in name_lower or 'luxury' in name_lower:
            fallback_rel = 'images/jewelry/earrings/rose_gold_earrings.webp'
        else:
            fallback_rel = 'images/jewelry/earrings/default_earring.webp'
    elif cat_lower == 'pendant':
        if 'diamond' in name_lower or 'elegant' in name_lower:
            fallback_rel = 'images/jewelry/pendants/elegant_diamond_pendant.webp'
        else:
            fallback_rel = 'images/jewelry/pendants/default_pendant.webp'
    elif cat_lower == 'chain':
        fallback_rel = 'images/jewelry/chains/default_chain.webp'
        
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src_path = os.path.join(base_dir, 'static', fallback_rel.replace('/', os.sep))
    
    if os.path.exists(src_path):
        import shutil
        try:
            shutil.copy2(src_path, filepath)
            print(f"  Coceeded: copied {fallback_rel} -> {os.path.basename(filepath)}")
        except Exception:
            pass


def _ensure_placeholder_image():
    """Create the generic jewellery placeholder if it doesn't exist."""
    placeholder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "img", "placeholder.png")
    if os.path.exists(placeholder):
        return
    os.makedirs(os.path.dirname(placeholder), exist_ok=True)
    if not HAS_PIL:
        return
    try:
        img = Image.new("RGB", (400, 300), color=(13, 13, 22))
        draw = ImageDraw.Draw(img)
        gold = (212, 175, 55)
        for i in range(3):
            draw.rectangle([i, i, 399 - i, 299 - i], outline=gold)
        font = ImageFont.load_default()
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except Exception:
            pass
        pts = [(200, 60), (240, 100), (225, 150), (175, 150), (160, 100)]
        draw.polygon(pts, outline=gold, width=3)
        bbox = draw.textbbox((0, 0), "Jewellery Image", font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((400 - tw) // 2, 175), "Jewellery Image", fill=gold, font=font)
        img.save(placeholder, "PNG")
    except Exception:
        pass


def get_db(app):
    """Return a new SQLite connection."""
    return sqlite3.connect(
        app.config['DATABASE_PATH'],
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )


def init_db(app):
    """Create all tables if they don't already exist."""
    conn = get_db(app)
    cur = conn.cursor()
    cur.executescript("""
    PRAGMA foreign_keys = ON;

    /* ── Employees (users / staff) ────────────────────────────── */
    CREATE TABLE IF NOT EXISTS employees (
        employee_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name          TEXT    NOT NULL,
        phone         TEXT,
        email         TEXT    UNIQUE,
        address       TEXT,
        role          TEXT    NOT NULL DEFAULT 'Staff',   -- Admin | Manager | Staff
        salary        REAL    DEFAULT 0,
        join_date     TEXT    DEFAULT (date('now')),
        password_hash TEXT    NOT NULL,
        is_active     INTEGER DEFAULT 1,
        created_at    TEXT    DEFAULT (datetime('now'))
    );

    /* ── Customers ────────────────────────────────────────────── */
    CREATE TABLE IF NOT EXISTS customers (
        customer_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        name           TEXT    NOT NULL,
        phone          TEXT,
        email          TEXT,
        address        TEXT,
        dob            TEXT,
        anniversary    TEXT,
        preferences    TEXT,                              -- JSON list
        loyalty_points INTEGER DEFAULT 0,
        created_at     TEXT    DEFAULT (datetime('now'))
    );

    /* ── Jewellery Items ──────────────────────────────────────── */
    CREATE TABLE IF NOT EXISTS jewellery_items (
        item_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        name           TEXT    NOT NULL,
        category       TEXT    NOT NULL,                  -- Ring|Necklace|Bracelet|Earrings|Other
        material       TEXT    DEFAULT 'Gold',            -- Gold|Silver|Platinum|Rose Gold
        purity         TEXT    DEFAULT '22K',
        weight_gm      REAL    DEFAULT 0,
        making_charges REAL    DEFAULT 0,
        cost_price     REAL    DEFAULT 0,
        selling_price  REAL    NOT NULL,
        stock_qty      INTEGER DEFAULT 0,
        barcode        TEXT    UNIQUE,
        image_path     TEXT,
        image_url      TEXT,
        barcode_image  TEXT,
        description    TEXT,
        supplier       TEXT    DEFAULT '',
        is_active      INTEGER DEFAULT 1,
        created_at     TEXT    DEFAULT (datetime('now'))
    );

    /* ── Sales ────────────────────────────────────────────────── */
    CREATE TABLE IF NOT EXISTS sales (
        sale_id         INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id     INTEGER REFERENCES customers(customer_id),
        employee_id     INTEGER REFERENCES employees(employee_id),
        sale_date       TEXT    DEFAULT (datetime('now')),
        subtotal        REAL    DEFAULT 0,
        discount        REAL    DEFAULT 0,
        gst_amount      REAL    DEFAULT 0,
        total_amount    REAL    DEFAULT 0,
        payment_method  TEXT    DEFAULT 'Cash',           -- Cash|Card|UPI|Cheque
        notes           TEXT,
        status          TEXT    DEFAULT 'Completed'
    );

    /* ── Sale Items (line items per sale) ────────────────────── */
    CREATE TABLE IF NOT EXISTS sale_items (
        sale_item_id  INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id       INTEGER NOT NULL REFERENCES sales(sale_id),
        item_id       INTEGER NOT NULL REFERENCES jewellery_items(item_id),
        quantity      INTEGER DEFAULT 1,
        unit_price    REAL    DEFAULT 0,
        total_price   REAL    DEFAULT 0
    );

    /* ── Bills ────────────────────────────────────────────────── */
    CREATE TABLE IF NOT EXISTS bills (
        bill_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id       INTEGER REFERENCES sales(sale_id),
        customer_id   INTEGER REFERENCES customers(customer_id),
        bill_number   TEXT    UNIQUE,
        bill_date     TEXT    DEFAULT (datetime('now')),
        subtotal      REAL    DEFAULT 0,
        cgst_amount   REAL    DEFAULT 0,
        sgst_amount   REAL    DEFAULT 0,
        gst_amount    REAL    DEFAULT 0,
        discount      REAL    DEFAULT 0,
        total_amount  REAL    DEFAULT 0,
        qr_code_path  TEXT,
        pdf_path      TEXT,
        email_sent    INTEGER DEFAULT 0,
        status        TEXT    DEFAULT 'Paid'
    );

    /* ── Feedback ─────────────────────────────────────────────── */
    CREATE TABLE IF NOT EXISTS feedback (
        feedback_id  INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id  INTEGER REFERENCES customers(customer_id),
        item_id      INTEGER REFERENCES jewellery_items(item_id),
        rating       INTEGER DEFAULT 5,
        comment      TEXT,
        created_at   TEXT    DEFAULT (datetime('now'))
    );

    /* ── Attendance ───────────────────────────────────────────── */
    CREATE TABLE IF NOT EXISTS attendance (
        attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id   INTEGER REFERENCES employees(employee_id),
        work_date     TEXT    NOT NULL,
        check_in      TEXT,
        check_out     TEXT,
        status        TEXT    DEFAULT 'Present',          -- Present|Absent|Half-Day|Leave
        notes         TEXT,
        UNIQUE(employee_id, work_date)
    );

    /* ── Salary Records ───────────────────────────────────────── */
    CREATE TABLE IF NOT EXISTS salary_records (
        record_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id  INTEGER REFERENCES employees(employee_id),
        month_year   TEXT    NOT NULL,
        base_salary  REAL    DEFAULT 0,
        bonus        REAL    DEFAULT 0,
        deductions   REAL    DEFAULT 0,
        net_salary   REAL    DEFAULT 0,
        paid_on      TEXT,
        status       TEXT    DEFAULT 'Pending'            -- Pending|Paid
    );

    /* ── App Settings (key‑value) ────────────────────────────── */
    CREATE TABLE IF NOT EXISTS app_settings (
        key   TEXT PRIMARY KEY,
        value TEXT
    );

    /* ── Indexes for performance ─────────────────────────────── */
    CREATE INDEX IF NOT EXISTS idx_sales_date      ON sales(sale_date);
    CREATE INDEX IF NOT EXISTS idx_sales_customer  ON sales(customer_id);
    CREATE INDEX IF NOT EXISTS idx_items_category  ON jewellery_items(category);
    CREATE INDEX IF NOT EXISTS idx_items_barcode   ON jewellery_items(barcode);
    CREATE INDEX IF NOT EXISTS idx_att_employee    ON attendance(employee_id);
    CREATE INDEX IF NOT EXISTS idx_att_date        ON attendance(work_date);
    """)
    
    # Check if image_url column exists in jewellery_items
    cur.execute("PRAGMA table_info(jewellery_items)")
    columns = [row[1] for row in cur.fetchall()]
    if 'image_url' not in columns:
        cur.execute("ALTER TABLE jewellery_items ADD COLUMN image_url TEXT")
        conn.commit()

    # Fix any image_url values that still have external URLs or /static/ prefix
    cur.execute("""
        UPDATE jewellery_items 
        SET image_url = REPLACE(image_url, '/static/', '')
        WHERE image_url LIKE '/static/%'
    """)
    
    # Backfill image_url from image_path for older items
    cur.execute("""
        UPDATE jewellery_items 
        SET image_url = image_path 
        WHERE (image_url IS NULL OR image_url = '') AND image_path IS NOT NULL AND image_path != ''
    """)
    
    conn.commit()
    conn.close()


def seed_demo_data(app):
    """Insert demo data if the employees table is empty."""
    conn = get_db(app)
    cur = conn.cursor()

    if cur.execute("SELECT COUNT(*) FROM employees").fetchone()[0] > 0:
        conn.close()
        return   # Already seeded

    print("  Seeding demo data …")

    # ── Employees ──────────────────────────────────────────────────
    employees = [
        ('Admin User',   '+91-9000000001', 'admin@shop.com',  'Admin',   75000, 'admin123'),
        ('Priya Sharma', '+91-9000000002', 'priya@shop.com',  'Manager', 45000, 'staff123'),
        ('Rahul Gupta',  '+91-9000000003', 'rahul@shop.com',  'Staff',   30000, 'staff123'),
        ('Sunita Patel', '+91-9000000004', 'sunita@shop.com', 'Staff',   28000, 'staff123'),
    ]
    for name, phone, email, role, salary, pwd in employees:
        hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
        cur.execute("""
            INSERT INTO employees (name, phone, email, role, salary, password_hash)
            VALUES (?,?,?,?,?,?)
        """, (name, phone, email, role, salary, hashed))

    # ── Customers ──────────────────────────────────────────────────
    customers = [
        ('Ananya Mehta',    '+91-9111111111', 'ananya@email.com',  '1990-05-14', '2015-11-20', '["Ring","Necklace"]',  120),
        ('Deepak Joshi',    '+91-9222222222', 'deepak@email.com',  '1985-08-22', None,         '["Bracelet"]',         80),
        ('Kavita Singh',    '+91-9333333333', 'kavita@email.com',  '1992-03-11', '2018-02-14', '["Earrings","Ring"]',  200),
        ('Mohan Verma',     '+91-9444444444', 'mohan@email.com',   '1978-12-05', '2005-06-01', '["Necklace"]',         50),
        ('Ritu Agarwal',    '+91-9555555555', 'ritu@email.com',    '1995-07-30', '2020-01-15', '["Ring","Earrings"]',  300),
        ('Suresh Kumar',    '+91-9666666666', 'suresh@email.com',  '1970-02-18', None,         '["Bracelet","Ring"]',  60),
        ('Pooja Desai',     '+91-9777777777', 'pooja@email.com',   '1998-09-25', '2022-03-08', '["Necklace","Ring"]',  150),
        ('Amit Choudhary',  '+91-9888888888', 'amit@email.com',    '1983-04-12', '2010-12-25', '["Bracelet"]',         90),
    ]
    for name, phone, email, dob, ann, prefs, pts in customers:
        cur.execute("""
            INSERT INTO customers (name, phone, email, dob, anniversary, preferences, loyalty_points)
            VALUES (?,?,?,?,?,?,?)
        """, (name, phone, email, dob, ann, prefs, pts))

    # ── Jewellery Items ────────────────────────────────────────────
    items = [
        ('Classic Gold Ring',       'Ring',      'Gold',     '22K', 5.2,  800,  12000, 15000, 10, 'JW-001', 'uploads/products/gold_ring.webp'),
        ('Diamond Solitaire Ring',  'Ring',      'Gold',     '18K', 4.5, 5000,  55000, 75000,  5, 'JW-002', 'uploads/products/diamond_ring.webp'),
        ('Gold Necklace Set',       'Necklace',  'Gold',     '22K',15.0, 2500,  45000, 55000,  8, 'JW-003', 'uploads/products/gold_necklace.webp'),
        ('Kundan Necklace',         'Necklace',  'Gold',     '18K',12.5, 3000,  38000, 48000,  4, 'JW-004', 'uploads/products/kundan_necklace.webp'),
        ('Gold Bangles Set (4pc)',   'Bracelet',  'Gold',     '22K',20.0, 1800,  55000, 65000,  6, 'JW-005', 'uploads/products/gold_bangles.webp'),
        ('Diamond Bracelet',        'Bracelet',  'Gold',     '18K', 8.0, 8000,  80000,110000,  3, 'JW-006', 'uploads/products/diamond_bracelet.webp'),
        ('Gold Jhumka Earrings',    'Earrings',  'Gold',     '22K', 6.0,  900,  16000, 20000, 15, 'JW-007', 'uploads/products/gold_earrings.webp'),
        ('Pearl Drop Earrings',     'Earrings',  'Gold',     '18K', 4.0, 2000,  18000, 24000,  7, 'JW-008', 'uploads/products/pearl_earrings.webp'),
        ('Silver Anklet',           'Bracelet',  'Silver',   '92.5', 18.0, 500,   2800,  4500, 20, 'JW-009', 'uploads/products/silver_anklet.webp'),
        ('Platinum Ring',           'Ring',      'Platinum', 'PT950', 4.0, 3000, 35000, 45000,  2, 'JW-010', 'uploads/products/platinum_ring.webp'),
        ('Rose Gold Earrings',      'Earrings',  'Rose Gold','18K', 3.5, 1200, 12000, 16000,  9, 'JW-011', 'uploads/products/rose_gold_earrings.webp'),
        ('Temple Necklace',         'Necklace',  'Gold',     '22K',18.0, 2000, 52000, 62000,  6, 'JW-012', 'uploads/products/temple_necklace.webp'),
        ('Mangalsutra',             'Necklace',  'Gold',     '22K',10.0, 1500, 28000, 35000, 12, 'JW-013', 'uploads/products/mangalsutra.webp'),
        ('Gold Kada',               'Bracelet',  'Gold',     '22K',25.0, 1000, 68000, 80000,  4, 'JW-014', 'uploads/products/gold_kada.webp'),
        ('Nose Pin',                'Other',     'Gold',     '22K', 1.0,  200,   2500,  3500, 25, 'JW-015', 'uploads/products/nose_pin.webp'),
        ('Diamond Eternity Ring',   'Ring',      'Platinum', 'PT950', 5.0, 6000, 110000, 145000, 3, 'JW-016', 'uploads/products/eternity_ring.webp'),
        ('Royal Diamond Necklace',  'Necklace',  'Platinum', 'PT950', 22.4, 15000, 280000, 360000, 2, 'JW-017', 'uploads/products/royal_necklace.webp'),
        ('Luxury Diamond Earrings', 'Earrings',  'White Gold','18K', 6.2, 4500, 42000, 60000,  4, 'JW-018', 'uploads/products/luxury_earrings.webp'),
        ('Elegant Diamond Pendant', 'Pendant',   'Gold',     '18K', 3.8, 2500, 22000, 32000,  7, 'JW-019', 'uploads/products/diamond_pendant.webp'),
        ('Diamond Bangle (Single)', 'Bangles',   'Platinum', 'PT950', 12.0, 5500, 85000, 115000, 5, 'JW-020', 'uploads/products/diamond_bangle.webp'),
    ]
    BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _ensure_placeholder_image()
    for name, cat, mat, pur, wt, mc, cp, sp, qty, bc, img in items:
        cur.execute("""
            INSERT INTO jewellery_items
              (name, category, material, purity, weight_gm, making_charges,
               cost_price, selling_price, stock_qty, barcode, image_path, image_url,
               description)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (name, cat, mat, pur, wt, mc, cp, sp, qty, bc, img, img,
              f'{mat} {cat} — {pur} purity, {wt}g'))
        _create_placeholder_image(os.path.join(BASE, "static", img.replace("/", os.sep)), name, cat)

    # ── Sales & Bills (last 6 months) ──────────────────────────────
    today = date.today()
    gst_rate = 3.0
    bill_counter = 1001

    item_rows = cur.execute(
        "SELECT item_id, selling_price FROM jewellery_items"
    ).fetchall()
    cust_ids = [r[0] for r in cur.execute("SELECT customer_id FROM customers").fetchall()]
    emp_ids  = [r[0] for r in cur.execute(
        "SELECT employee_id FROM employees WHERE role != 'Admin'").fetchall()]

    for days_back in range(180, 0, -3):
        sale_date = today - timedelta(days=days_back)
        n_sales = random.randint(1, 3)
        for _ in range(n_sales):
            cid = random.choice(cust_ids)
            eid = random.choice(emp_ids)
            item_id, sp = random.choice(item_rows)
            qty = random.randint(1, 2)
            subtotal = sp * qty
            discount = subtotal * random.uniform(0, 0.05)
            gst = (subtotal - discount) * gst_rate / 100
            total = subtotal - discount + gst

            cur.execute("""
                INSERT INTO sales
                  (customer_id, employee_id, sale_date, subtotal, discount,
                   gst_amount, total_amount, payment_method, status)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (cid, eid, sale_date.strftime('%Y-%m-%d %H:%M:%S'),
                  round(subtotal, 2), round(discount, 2),
                  round(gst, 2), round(total, 2),
                  random.choice(['Cash', 'Card', 'UPI']), 'Completed'))
            sale_id = cur.lastrowid

            cur.execute("""
                INSERT INTO sale_items (sale_id, item_id, quantity, unit_price, total_price)
                VALUES (?,?,?,?,?)
            """, (sale_id, item_id, qty, sp, round(sp * qty, 2)))

            cgst = gst / 2
            sgst = gst / 2
            bill_no = f'BILL-{bill_counter:05d}'
            bill_counter += 1
            cur.execute("""
                INSERT INTO bills
                  (sale_id, customer_id, bill_number, bill_date, subtotal,
                   cgst_amount, sgst_amount, gst_amount, discount, total_amount, status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (sale_id, cid, bill_no,
                  sale_date.strftime('%Y-%m-%d %H:%M:%S'),
                  round(subtotal, 2), round(cgst, 2), round(sgst, 2),
                  round(gst, 2), round(discount, 2), round(total, 2), 'Paid'))

    # ── Feedback ───────────────────────────────────────────────────
    for _ in range(30):
        cur.execute("""
            INSERT INTO feedback (customer_id, item_id, rating, comment)
            VALUES (?,?,?,?)
        """, (random.choice(cust_ids),
              random.choice([r[0] for r in item_rows]),
              random.randint(3, 5),
              random.choice([
                  'Beautiful piece! Very happy.',
                  'Excellent craftsmanship.',
                  'Great quality gold.',
                  'Worth every rupee.',
                  'Loved it, will buy again.',
                  'Perfect gift for my wife.',
              ])))

    # ── Attendance (last 30 days) ──────────────────────────────────
    all_emp_ids = [r[0] for r in cur.execute("SELECT employee_id FROM employees").fetchall()]
    for days_back in range(30, 0, -1):
        att_date = (today - timedelta(days=days_back)).strftime('%Y-%m-%d')
        for eid in all_emp_ids:
            status = random.choices(
                ['Present', 'Present', 'Present', 'Present', 'Absent', 'Half-Day'],
                weights=[6, 6, 6, 6, 1, 1]
            )[0]
            ci = f'09:{random.randint(0,30):02d}' if status != 'Absent' else None
            co = f'18:{random.randint(0,30):02d}' if status == 'Present' else None
            try:
                cur.execute("""
                    INSERT OR IGNORE INTO attendance
                      (employee_id, work_date, check_in, check_out, status)
                    VALUES (?,?,?,?,?)
                """, (eid, att_date, ci, co, status))
            except Exception:
                pass

    conn.commit()
    conn.close()
    print("  ✓ Demo data seeded successfully.")
