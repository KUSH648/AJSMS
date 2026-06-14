"""
modules/sales.py
================
Sales reporting, profit calculation, and analysis helpers.
"""

from datetime import datetime, date, timedelta
from database.models import query


def get_sales_summary(period='today'):
    """Return summary stats for a given period."""
    today = date.today().isoformat()
    month = today[:7]
    year  = today[:4]

    if period == 'today':
        cond = "date(sale_date) = ?"
        arg  = today
    elif period == 'month':
        cond = "strftime('%Y-%m', sale_date) = ?"
        arg  = month
    elif period == 'year':
        cond = "strftime('%Y', sale_date) = ?"
        arg  = year
    else:
        cond = "1=1"
        arg  = None

    args = (arg,) if arg else ()
    row = query(f"""
        SELECT COALESCE(SUM(total_amount),0)  AS revenue,
               COALESCE(SUM(gst_amount),0)    AS gst,
               COALESCE(SUM(discount),0)      AS discount,
               COALESCE(SUM(subtotal),0)       AS subtotal,
               COUNT(*)                        AS orders
        FROM sales
        WHERE {cond}
    """, args, one=True)
    return row


def get_profit_analysis(start_date=None, end_date=None):
    """Calculate profit = revenue - cost of goods sold."""
    if not start_date:
        start_date = (date.today() - timedelta(days=30)).isoformat()
    if not end_date:
        end_date = date.today().isoformat()

    rows = query("""
        SELECT s.sale_date,
               si.quantity,
               si.unit_price,
               si.total_price,
               ji.cost_price,
               ji.making_charges,
               ji.name  AS item_name,
               ji.category
        FROM sales s
        JOIN sale_items si ON s.sale_id = si.sale_id
        JOIN jewellery_items ji ON si.item_id = ji.item_id
        WHERE date(s.sale_date) BETWEEN ? AND ?
    """, (start_date, end_date))

    total_revenue = 0.0
    total_cost    = 0.0
    for r in rows:
        total_revenue += r['total_price']
        total_cost    += (r['cost_price'] + r['making_charges']) * r['quantity']

    profit     = total_revenue - total_cost
    margin_pct = (profit / total_revenue * 100) if total_revenue else 0

    return {
        'start_date':    start_date,
        'end_date':      end_date,
        'total_revenue': round(total_revenue, 2),
        'total_cost':    round(total_cost,    2),
        'gross_profit':  round(profit,        2),
        'margin_pct':    round(margin_pct,    2),
        'line_items':    rows,
    }


def get_daily_sales_chart(days=30):
    """Return day-by-day totals for chart rendering."""
    return query("""
        SELECT date(sale_date)       AS day,
               SUM(total_amount)     AS revenue,
               SUM(gst_amount)       AS gst,
               COUNT(*)              AS orders
        FROM sales
        WHERE date(sale_date) >= date('now', ?)
        GROUP BY day
        ORDER BY day
    """, (f'-{days} days',))


def get_payment_method_breakdown(month_year=None):
    """Breakdown of payment methods."""
    if not month_year:
        month_year = date.today().strftime('%Y-%m')
    return query("""
        SELECT payment_method,
               COUNT(*)            AS count,
               SUM(total_amount)   AS total
        FROM sales
        WHERE strftime('%Y-%m', sale_date) = ?
        GROUP BY payment_method
    """, (month_year,))


def get_top_customers(limit=10):
    return query("""
        SELECT c.customer_id, c.name, c.phone,
               COUNT(s.sale_id)      AS orders,
               SUM(s.total_amount)   AS spent
        FROM sales s
        JOIN customers c ON s.customer_id = c.customer_id
        GROUP BY c.customer_id
        ORDER BY spent DESC
        LIMIT ?
    """, (limit,))


def get_employee_sales_performance(month_year=None):
    if not month_year:
        month_year = date.today().strftime('%Y-%m')
    return query("""
        SELECT e.employee_id, e.name, e.role,
               COUNT(s.sale_id)    AS orders,
               SUM(s.total_amount) AS revenue
        FROM sales s
        JOIN employees e ON s.employee_id = e.employee_id
        WHERE strftime('%Y-%m', s.sale_date) = ?
        GROUP BY e.employee_id
        ORDER BY revenue DESC
    """, (month_year,))
