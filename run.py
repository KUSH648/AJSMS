"""
AI-Powered Jewellery Shop Management System
============================================
Entry point — run this file to start the application.

Usage:
    python run.py

Default: http://127.0.0.1:5000
Admin login: admin / admin123
"""

from app import create_app
from database.db_setup import init_db, seed_demo_data
from utils.image_manager import assign_images_to_all_products
import os

app = create_app()

if __name__ == '__main__':
    # Create upload folder if missing
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('static/bills', exist_ok=True)
    os.makedirs('ml_models', exist_ok=True)

    with app.app_context():
        init_db(app)          # Create all tables
        seed_demo_data(app)   # Insert demo data on first run
        assign_images_to_all_products(app)  # Ensure all products have valid images

    print("=" * 55)
    print("  [*] JewelHub - Jewellery Management System [*]")
    print("=" * 55)
    print("  URL  :  http://127.0.0.1:5000")
    print("  Admin:  admin / admin123")
    print("  Staff:  staff1 / staff123")
    print("=" * 55)

    app.run(debug=True, host='0.0.0.0', port=5000)
