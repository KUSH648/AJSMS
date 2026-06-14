def get_active_notifications():
    from database.models import get_low_stock_items, get_upcoming_birthdays
    notifications = []
    
    # 1. Low stock items
    try:
        low_stock = get_low_stock_items(threshold=5)
        for item in low_stock:
            notifications.append({
                'type': 'warning',
                'message': f"Low stock alert: {item['name']} (only {item['stock_qty']} left)",
                'icon': 'exclamation-triangle',
                'color': 'warning'
            })
    except Exception as e:
        print(f"Error fetching low stock notifications: {e}")
        
    # 2. Upcoming birthdays
    try:
        birthdays = get_upcoming_birthdays(days=7)
        for customer in birthdays:
            notifications.append({
                'type': 'info',
                'message': f"🎂 Birthday reminder: {customer['name']}'s birthday is on {customer['dob']}",
                'icon': 'birthday-cake',
                'color': 'info'
            })
    except Exception as e:
        print(f"Error fetching birthday notifications: {e}")
        
    return notifications
