"""
Routes Package — registers all Flask Blueprints
"""
from .auth_routes import auth_bp
from .dashboard_routes import dashboard_bp
from .inventory_routes import inventory_bp
from .customer_routes import customer_bp
from .billing_routes import billing_bp
from .sales_routes import sales_bp
from .employee_routes import employee_bp
from .ai_routes import ai_bp
from .api_routes import api_bp

__all__ = [
    'auth_bp', 'dashboard_bp', 'inventory_bp', 'customer_bp',
    'billing_bp', 'sales_bp', 'employee_bp', 'ai_bp', 'api_bp'
]