"""
routes/api_routes.py
====================
General-purpose API endpoints: gold prices, notifications, health check.
"""
from flask import Blueprint, jsonify, current_app
from flask_login import login_required
from datetime import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api')

# ── Hardcoded fallback gold rates (Indian market, per gram) ──────────────
FALLBACK_GOLD_RATES = {
    '24K': 7250,
    '22K': 6640,
    '18K': 5440,
    'Silver': 88,
    'Platinum': 3100,
}


@api_bp.route('/gold-price')
@login_required
def gold_price():
    """Return live gold/silver prices.

    Tries to fetch from a free API if a GOLD_API_KEY is configured,
    otherwise falls back to approximate hardcoded rates.
    """
    import os
    api_key = os.environ.get('GOLD_API_KEY', current_app.config.get('GOLD_API_KEY', ''))

    rates = dict(FALLBACK_GOLD_RATES)
    source = 'fallback'
    updated_at = datetime.now().strftime('%Y-%m-%d %H:%M')

    if api_key:
        try:
            import requests
            resp = requests.get(
                'https://www.goldapi.io/api/XAU/INR',
                headers={'x-access-token': api_key},
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                # goldapi returns price per troy ounce — convert to per gram
                per_gram_24k = round(data.get('price', 0) / 31.1035, 2)
                rates['24K'] = per_gram_24k
                rates['22K'] = round(per_gram_24k * 0.916, 2)
                rates['18K'] = round(per_gram_24k * 0.750, 2)
                source = 'goldapi.io'
                updated_at = data.get('timestamp', updated_at)
        except Exception:
            pass  # Fall through to fallback

    return jsonify({
        'rates': rates,
        'source': source,
        'updated_at': updated_at,
        'currency': 'INR',
    })


@api_bp.route('/low-stock')
@login_required
def low_stock():
    """Return items below the low-stock threshold."""
    from database.models import get_low_stock_items
    threshold = current_app.config.get('LOW_STOCK_THRESHOLD', 3)
    items = get_low_stock_items(threshold)
    return jsonify({'items': items, 'count': len(items)})


@api_bp.route('/notifications')
@login_required
def notifications():
    """Return all active notifications (low stock, birthdays, etc.)."""
    from modules.notifications import get_active_notifications
    notifs = get_active_notifications()
    return jsonify({'notifications': notifs, 'count': len(notifs)})


@api_bp.route('/health')
def health_check():
    """Simple health-check endpoint for deployment monitoring."""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})
