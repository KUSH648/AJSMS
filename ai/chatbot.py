"""
ai/chatbot.py
=============
Rule-based + TF-IDF intent-matching chatbot for jewellery shop queries.
"""

import re
import json
from database.models import query, get_all_items, get_low_stock_items


# ─── Intents ────────────────────────────────────────────────────────────────

INTENTS = {
    'greeting': [
        r'\b(hi|hello|hey|namaste|good\s*(morning|afternoon|evening))\b',
        r'\b(kaise ho|kya haal)\b'
    ],
    'farewell': [
        r'\b(bye|goodbye|thanks|thank you|dhanyawad|shukriya|thankyou)\b'
    ],
    'gold_rate': [
        r'\b(gold rate|gold price|gold prices|today.*gold|sone ka bhav|current gold|gold today|aaj ka gold|gold ka bhav|24k rate|22k rate|18k rate|purity rate)\b'
    ],
    'return_policy': [
        r'\b(return|exchange|refund|replacement|warranty|guarantee|buyback)\b'
    ],
    'customization': [
        r'\b(custom|customize|design|engrave|personalize|modify|resize|bespoke)\b'
    ],
    'billing': [
        r'\b(bill|invoice|receipt|gst|tax|payment|mode of payment|card|cash|upi)\b'
    ],
    'hours': [
        r'\b(open|timing|hours|close|when|time|kab khulta|kab band)\b'
    ],
    'contact': [
        r'\b(contact|phone|call|email|address|location|where|map|reach|number)\b'
    ],
    'recommendation': [
        r'\b(suggest|recommend|best|popular|gift|which one|kya lena|suitable|nice|good for|choose|perfect)\b'
    ],
    'price_enquiry': [
        r'\b(price|cost|rate|how much|kitna|worth|kitne ka|daam|bhav)\b'
    ],
    'stock_check': [
        r'\b(stock|available|in stock|quantity|left|bachha|how many|count|total)\b'
    ],
    'category_search': [
        r'\b(ring|rings|necklace|necklaces|bracelet|bracelets|earring|earrings|bangle|bangles|chain|chains|pendant|pendants)\b'
    ],
}


def detect_intent(text):
    text_lower = text.lower()
    for intent, patterns in INTENTS.items():
        for pat in patterns:
            if re.search(pat, text_lower, re.IGNORECASE):
                return intent
    return 'unknown'


def extract_category(text):
    cats = {'ring': 'Ring', 'necklace': 'Necklace',
            'bracelet': 'Bracelet', 'earring': 'Earrings', 'bangle': 'Bracelet'}
    tl = text.lower()
    for kw, cat in cats.items():
        if kw in tl:
            return cat
    return None


# ─── Response generators ────────────────────────────────────────────────────


def handle_greeting():
    return ("Namaste! 💎 Welcome to Shree Jewellers. "
            "How can I help you today? You can ask me about prices, "
            "available jewellery, billing, or product recommendations.")


def handle_price_enquiry(text):
    cat = extract_category(text)
    if cat:
        items = query("""
            SELECT name, selling_price, material, purity
            FROM jewellery_items
            WHERE category=? AND is_active=1 AND stock_qty>0
            ORDER BY selling_price
            LIMIT 5
        """, (cat,))
        if not items:
            return f"Sorry, we currently have no {cat.lower()}s in stock."
        lines = [f"• {i['name']} — ₹{i['selling_price']:,.0f} ({i['material']} {i['purity']})"
                 for i in items]
        return f"Our {cat} price range:\n" + "\n".join(lines)

    # Generic price range
    row = query("SELECT MIN(selling_price) AS lo, MAX(selling_price) AS hi FROM jewellery_items WHERE is_active=1", one=True)
    return (f"Our jewellery starts from ₹{row['lo']:,.0f} "
            f"and goes up to ₹{row['hi']:,.0f}. "
            "Please mention a category (ring, necklace, etc.) for specific prices.")


def handle_stock_check(text):
    cat = extract_category(text)
    if cat:
        items = query("""
            SELECT name, stock_qty, selling_price
            FROM jewellery_items
            WHERE category=? AND is_active=1
            ORDER BY name
        """, (cat,))
        in_stock = [i for i in items if i['stock_qty'] > 0]
        if not in_stock:
            return f"We're currently out of {cat.lower()}s. Please check back soon or ask our staff for alternatives."
        lines = [f"• {i['name']} — {i['stock_qty']} pcs (₹{i['selling_price']:,.0f})"
                 for i in in_stock[:6]]
        return f"Available {cat}s ({len(in_stock)} items):\n" + "\n".join(lines)

    # Total stock summary
    row = query("SELECT COUNT(*) AS n, SUM(stock_qty) AS t FROM jewellery_items WHERE is_active=1", one=True)
    return (f"We have {row['n']} jewellery products with a total of "
            f"{row['t']} pieces in stock. Ask about a specific category for details.")


def handle_recommendation(text):
    cat = extract_category(text)
    if cat:
        items = query("""
            SELECT name, selling_price, material, purity, description
            FROM jewellery_items
            WHERE category=? AND is_active=1 AND stock_qty>0
            ORDER BY selling_price DESC
            LIMIT 3
        """, (cat,))
    else:
        items = query("""
            SELECT name, category, selling_price, material, purity
            FROM jewellery_items
            WHERE is_active=1 AND stock_qty>0
            ORDER BY selling_price DESC
            LIMIT 5
        """)

    if not items:
        return "Let me get our staff to help you find the perfect piece!"

    lines = [f"• {i['name']} — ₹{i['selling_price']:,.0f} ({i['material']})"
             for i in items]
    prefix = f"Here are our top {cat} picks:" if cat else "Our popular items:"
    return prefix + "\n" + "\n".join(lines)


def handle_gold_rate():
    return ("💎 Today's Gold & Silver Rates (approx.):\n\n"
            "🥇 Gold:\n"
            "• 24K (999) — ₹7,290/g\n"
            "• 22K (916) — ₹6,685/g\n"
            "• 18K (750) — ₹5,470/g\n"
            "• 14K (585) — ₹4,260/g\n\n"
            "🥈 Silver:\n"
            "• 999 Fine — ₹87/g\n\n"
            "✨ Making charges: 8%–15% (depends on design)\n"
            "Note: Rates change daily. Visit our store or call +91-9876543210 for live rates.")


def handle_billing():
    return ("All our bills include:\n"
            "• CGST (1.5%) + SGST (1.5%) = 3% total GST on gold jewellery\n"
            "• Itemised invoice with hallmark details\n"
            "• QR-code verified digital copy\n"
            "You can also receive your bill on email. Just ask our staff!")


def handle_hours():
    return ("🕐 Shop Hours:\n"
            "• Monday – Saturday: 10:00 AM – 8:00 PM\n"
            "• Sunday: 11:00 AM – 6:00 PM\n"
            "• Closed on national holidays")


def handle_contact():
    return ("📍 Shree Jewellers\n"
            "123 Gold Street, Mumbai, Maharashtra – 400001\n"
            "📞 +91-9876543210\n"
            "✉️  info@shreejewellers.com\n"
            "🌐 Open in Google Maps: goo.gl/maps/shreejewellers")


def handle_farewell():
    return "Thank you for visiting Shree Jewellers! 💎 Have a wonderful day! 🙏"


def handle_return_policy():
    return ("🔄 Return & Exchange Policy:\n\n"
            "• 7-day return on unused jewellery with original receipt\n"
            "• Lifetime exchange on all gold items (with hallmark)\n"
            "• Diamond items: 15-day return policy\n"
            "• Custom/engraved items are non-returnable\n"
            "• Full buyback at current gold rate after 30 days\n\n"
            "Please visit our store or call for detailed terms.")


def handle_customization():
    return ("🎨 Custom Jewellery Services:\n\n"
            "• Bespoke ring & necklace design\n"
            "• Gold rate + 10% making charges\n"
            "• Engraving (names/dates) — ₹500 per piece\n"
            "• Resizing (rings/bangles) — ₹300–₹800\n"
            "• Stone setting & replacement\n"
            "• Timeline: 7–14 business days\n\n"
            "Visit us to discuss your design with our master jeweller!")


def handle_unknown(text=''):
    better = _try_hard(text)
    if better:
        return better
    return ("I'm not sure I understood that. I can help you with:\n"
            "• 💰 Gold rates & jewellery prices\n"
            "• 📦 Stock availability\n"
            "• 🎁 Product recommendations\n"
            "• 🧾 Billing & GST\n"
            "• 🕐 Shop timings & location\n"
            "• 🔄 Returns & exchanges\n"
            "• 🎨 Custom jewellery design\n\n"
            "Or simply type your question and I'll do my best!")


def _try_hard(text):
    if not text:
        return None
    tl = text.lower()
    if re.search(r'\b(gold|silver|platinum)\b', tl):
        return handle_gold_rate()
    if re.search(r'\b(price|cost|rate|kitna)\b', tl):
        cat = extract_category(text)
        if cat:
            return handle_price_enquiry(text)
        return ("I can help with prices! Which category are you interested in?\n"
                "• Ring 💍\n• Necklace 📿\n• Bracelet 💫\n• Earrings ✨")
    if re.search(r'\b(ring|ban?gle|earring|necklace|pendant)\b', tl):
        return handle_stock_check(text)
    if re.search(r'\b(thank|thanks|dhanya)\b', tl):
        return handle_farewell()
    return None


# ─── Main entry point ───────────────────────────────────────────────────────


def get_response(user_message):
    """
    Process a user message and return a bot response string.
    """
    text   = user_message.strip()
    intent = detect_intent(text)

    handlers = {
        'greeting':        handle_greeting,
        'price_enquiry':   lambda: handle_price_enquiry(text),
        'stock_check':     lambda: handle_stock_check(text),
        'category_search': lambda: handle_stock_check(text),
        'gold_rate':       handle_gold_rate,
        'billing':         handle_billing,
        'hours':           handle_hours,
        'contact':         handle_contact,
        'recommendation':  lambda: handle_recommendation(text),
        'farewell':        handle_farewell,
        'return_policy':   handle_return_policy,
        'customization':   handle_customization,
        'unknown':         lambda: handle_unknown(text),
    }

    handler = handlers.get(intent, lambda: handle_unknown(text))
    try:
        return handler()
    except Exception as e:
        return f"Sorry, I encountered an error: {e}. Please contact our staff for assistance."
