"""
Sales Routes — daily/monthly reports, profit calculation, export, chart APIs
"""
from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required
from datetime import datetime, timedelta, date
import os
import calendar

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')


def calc_daily_profit(report_date):
    """Calculate total profit for a single day."""
    from modules.sales import get_profit_analysis
    return get_profit_analysis(report_date, report_date)


def calc_monthly_profit(month, year):
    """Calculate total profit for a given month."""
    from modules.sales import get_profit_analysis
    last_day = calendar.monthrange(year, month)[1]
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day:02d}"
    return get_profit_analysis(start_date, end_date)


# ── Daily report ──────────────────────────────────────────────────────────────
@sales_bp.route('/daily')
@login_required
def daily_report():
    from database.models import get_daily_sales, get_sales_by_date, query as _q

    report_date = request.args.get('date', '')
    if not report_date:
        last_sale = _q("SELECT date(max(sale_date)) as d FROM sales", one=True)
        report_date = last_sale['d'] if last_sale and last_sale['d'] else str(date.today())
    sales       = get_sales_by_date(report_date)
    summary     = get_daily_sales(report_date)
    profit_info = calc_daily_profit(report_date)

    return render_template('sales/daily.html',
                           sales=sales, summary=summary,
                           profit_info=profit_info, report_date=report_date)


# ── Monthly report ────────────────────────────────────────────────────────────
@sales_bp.route('/monthly')
@login_required
def monthly_report():
    from database.models import get_monthly_sales, get_monthly_summary

    today   = date.today()
    month   = int(request.args.get('month', today.month))
    year    = int(request.args.get('year',  today.year))

    daily_breakdown = get_monthly_sales(month, year)
    summary         = get_monthly_summary(month, year)
    profit_info     = calc_monthly_profit(month, year)

    # Chart: daily revenue within the month
    labels = [str(r['day']) for r in daily_breakdown]
    values = [float(r['total']) for r in daily_breakdown]

    return render_template('sales/monthly.html',
                           daily_breakdown=daily_breakdown,
                           summary=summary, profit_info=profit_info,
                           month=month, year=year,
                           chart_labels=labels, chart_values=values,
                           months=list(range(1, 13)),
                           years=list(range(today.year - 3, today.year + 1)))


# ── Yearly overview ───────────────────────────────────────────────────────────
@sales_bp.route('/yearly')
@login_required
def yearly_report():
    from database.models import get_yearly_sales
    year    = int(request.args.get('year', date.today().year))
    data    = get_yearly_sales(year)
    labels  = [r['month_name'] for r in data]
    values  = [float(r['total']) for r in data]
    return render_template('sales/yearly.html', data=data, year=year,
                           chart_labels=labels, chart_values=values)


# ── Export sales ──────────────────────────────────────────────────────────────
@sales_bp.route('/export')
@login_required
def export_sales():
    try:
        from database.models import get_all_sales_in_range
        from modules.excel_export import export_sales_to_excel
        date_from = request.args.get('from', str(date.today() - timedelta(days=30)))
        date_to   = request.args.get('to',   str(date.today()))
        sales     = get_all_sales_in_range(date_from, date_to)
        filepath  = export_sales_to_excel(sales, date_from, date_to)
        return send_file(filepath, as_attachment=True,
                         download_name=f'sales_{date_from}_to_{date_to}.xlsx',
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        flash(f'Export error: {str(e)}', 'danger')
        return redirect(url_for('sales.daily_report'))


# ── AJAX: chart data ──────────────────────────────────────────────────────────
@sales_bp.route('/api/weekly-chart')
@login_required
def api_weekly_chart():
    from database.models import get_daily_sales_range
    today = date.today()
    start = today - timedelta(days=6)
    rows  = get_daily_sales_range(str(start), str(today))
    return jsonify({'labels': [r['date'] for r in rows],
                    'values': [float(r['total']) for r in rows]})


@sales_bp.route('/api/top-items')
@login_required
def api_top_items():
    from database.models import get_top_selling_items
    limit = int(request.args.get('limit', 5))
    items = get_top_selling_items(limit=limit)
    return jsonify({'items': items})


@sales_bp.route('/api/category-revenue')
@login_required
def api_category_revenue():
    from database.models import get_revenue_by_category
    data = get_revenue_by_category()
    return jsonify({'labels': [r['category'] for r in data],
                    'values': [float(r['revenue']) for r in data]})