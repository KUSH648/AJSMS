"""
Dashboard Routes — home page, KPIs, analytics data
"""
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/')


@dashboard_bp.route('/')
@login_required
def index():
    from database.models import (
        get_dashboard_stats, get_low_stock_items,
        get_recent_sales, get_monthly_revenue_chart,
        get_top_selling_items, get_upcoming_birthdays
    )
    from modules.notifications import get_active_notifications

    stats          = get_dashboard_stats()
    low_stock      = get_low_stock_items(threshold=5)
    recent_sales   = get_recent_sales(limit=8)
    top_items      = get_top_selling_items(limit=5)
    notifications  = get_active_notifications()
    birthdays      = get_upcoming_birthdays(days=7)

    # Chart data (7-day sales trend)
    chart_data = get_monthly_revenue_chart()

    return render_template(
        'dashboard.html',
        stats=stats,
        low_stock=low_stock,
        recent_sales=recent_sales,
        top_items=top_items,
        notifications=notifications,
        birthdays=birthdays,
        chart_labels=json.dumps(chart_data.get('labels', [])),
        chart_values=json.dumps(chart_data.get('values', [])),
        now=datetime.now()
    )


# ── AJAX endpoints for live dashboard refresh ─────────────────────────────────
@dashboard_bp.route('/api/stats')
@login_required
def api_stats():
    from database.models import get_dashboard_stats
    return jsonify(get_dashboard_stats())


@dashboard_bp.route('/api/sales-chart')
@login_required
def api_sales_chart():
    """Returns last 30 days of daily sales totals."""
    from database.models import get_daily_sales_range
    today = datetime.today().date()
    start = today - timedelta(days=29)
    rows  = get_daily_sales_range(str(start), str(today))
    labels = [r['date'] for r in rows]
    values = [float(r['total']) for r in rows]
    return jsonify({'labels': labels, 'values': values})


@dashboard_bp.route('/api/category-pie')
@login_required
def api_category_pie():
    """Returns sales count grouped by jewellery category."""
    from database.models import get_sales_by_category
    rows = get_sales_by_category()
    return jsonify({'labels': [r['category'] for r in rows],
                    'values': [r['count'] for r in rows]})


@dashboard_bp.route('/api/low-stock')
@login_required
def api_low_stock():
    from database.models import get_low_stock_items
    items = get_low_stock_items(threshold=5)
    return jsonify({'items': items, 'count': len(items)})