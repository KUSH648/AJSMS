"""config.py — Application configuration."""

import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # ── Security ──────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY', 'jewellery-shop-ai-secret-2024-!@#xyz')

    # ── Database ──────────────────────────────────────────────────────
    DATABASE_PATH = os.path.join(BASE_DIR, 'jewellery_shop.db')

    # ── File uploads ─────────────────────────────────────────────────
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024   # 16 MB

    # ── Email (SMTP) ─────────────────────────────────────────────────
    MAIL_SERVER   = os.environ.get('MAIL_SERVER',   'smtp.gmail.com')
    MAIL_PORT     = int(os.environ.get('MAIL_PORT',  587))
    MAIL_USE_TLS  = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')

    # ── Shop information ─────────────────────────────────────────────
    SHOP_NAME    = os.environ.get('SHOP_NAME',    'Shree Jewellers')
    SHOP_ADDRESS = os.environ.get('SHOP_ADDRESS', '123 Gold Street, Mumbai, Maharashtra – 400001')
    SHOP_PHONE   = os.environ.get('SHOP_PHONE',   '+91-9876543210')
    SHOP_EMAIL   = os.environ.get('SHOP_EMAIL',   'info@shreejewellers.com')
    SHOP_GSTIN   = os.environ.get('SHOP_GSTIN',   '27AAPCA1234A1Z5')
    SHOP_PAN     = os.environ.get('SHOP_PAN',     'AAPCA1234A')

    # ── Tax ───────────────────────────────────────────────────────────
    GST_RATE    = 3.0    # % GST on gold jewellery (India)
    CGST_RATE   = 1.5
    SGST_RATE   = 1.5

    # ── ML ────────────────────────────────────────────────────────────
    ML_MODELS_DIR = os.path.join(BASE_DIR, 'ml_models')

    # ── Low-stock threshold ──────────────────────────────────────────
    LOW_STOCK_THRESHOLD = 3
