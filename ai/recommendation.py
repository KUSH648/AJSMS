"""
ai/recommendation.py
====================
Content-based jewellery recommendation engine using cosine similarity.
Improved to handle edge cases and return recommendations properly.
"""

import json
import numpy as np
from database.models import query, get_all_items, get_customer_by_id


CATEGORY_WEIGHTS = {
    'Ring':     [1, 0, 0, 0, 0],
    'Necklace': [0, 1, 0, 0, 0],
    'Bracelet': [0, 0, 1, 0, 0],
    'Earrings': [0, 0, 0, 1, 0],
    'Other':    [0, 0, 0, 0, 1],
}

MATERIAL_WEIGHTS = {
    'Gold':       [1, 0, 0, 0, 0],
    'Silver':     [0, 1, 0, 0, 0],
    'Platinum':   [0, 0, 1, 0, 0],
    'Rose Gold':  [0, 0, 0, 1, 0],
    'White Gold': [0, 0, 0, 0, 1],
}


def item_to_vector(item):
    """Convert a jewellery item dict to a feature vector."""
    cat_vec = CATEGORY_WEIGHTS.get(item.get('category', 'Other'), [0]*5)
    mat_vec = MATERIAL_WEIGHTS.get(item.get('material', 'Gold'),   [0]*5)
    price_norm = min(item.get('selling_price', 0) / 500000.0, 1.0)
    weight_norm = min(item.get('weight_gm', 0) / 100.0, 1.0)
    return np.array(cat_vec + mat_vec + [price_norm, weight_norm])


def cosine_similarity(a, b):
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def get_similar_items(item_id, top_n=5):
    """Return top-N most similar items to the given item."""
    items = get_all_items()
    target = next((i for i in items if i['item_id'] == item_id), None)
    if not target:
        return []
    target_vec = item_to_vector(target)
    scored = []
    for item in items:
        if item['item_id'] == item_id or item['stock_qty'] == 0:
            continue
        sim = cosine_similarity(target_vec, item_to_vector(item))
        scored.append((sim, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [dict(item) for _, item in scored[:top_n]]


def recommend_for_customer(customer_id, top_n=6):
    """
    Recommend items based on customer preferences and purchase history.
    Falls back to top-rated / in-stock items if no history.
    """
    customer = get_customer_by_id(customer_id)
    preferred_cats = []
    if customer:
        try:
            preferred_cats = json.loads(customer.get('preferences') or '[]')
        except (json.JSONDecodeError, TypeError):
            preferred_cats = []

    bought = query("""
        SELECT DISTINCT si.item_id
        FROM sales s
        JOIN sale_items si ON s.sale_id = si.sale_id
        WHERE s.customer_id = ?
    """, (customer_id,))
    bought_ids = {r['item_id'] for r in bought}

    all_items = get_all_items()
    available = [i for i in all_items
                 if i['stock_qty'] > 0 and i['item_id'] not in bought_ids]

    if preferred_cats:
        def score(item):
            cat_bonus = 3.0 if item['category'] in preferred_cats else 0.0
            price_norm = item['selling_price'] / 100000.0
            return cat_bonus + price_norm
        available.sort(key=score, reverse=True)
    else:
        available.sort(key=lambda i: i['stock_qty'], reverse=True)

    if not available:
        available = [i for i in all_items if i['stock_qty'] > 0][:top_n]

    return [dict(item) for item in available[:top_n]]


def recommend_by_budget(budget, preferred_category=None, top_n=6):
    """Recommend items within a given budget."""
    items = get_all_items()
    filtered = [i for i in items
                if i['selling_price'] <= budget and i['stock_qty'] > 0]
    if preferred_category:
        pref = [i for i in filtered if i['category'] == preferred_category]
        rest = [i for i in filtered if i['category'] != preferred_category]
        filtered = pref + rest
    filtered.sort(key=lambda i: i['selling_price'], reverse=True)
    return [dict(item) for item in filtered[:top_n]]
