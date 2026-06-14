"""app.py — Flask application factory."""

from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
import os

login_manager = LoginManager()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload dirs exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('static/bills', exist_ok=True)

    # Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        from modules.auth import get_employee_by_id
        return get_employee_by_id(int(user_id))

    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.inventory_routes import inventory_bp
    from routes.customer_routes import customer_bp
    from routes.billing_routes import billing_bp
    from routes.sales_routes import sales_bp
    from routes.employee_routes import employee_bp
    from routes.ai_routes import ai_bp
    from routes.api_routes import api_bp
    from routes.settings_routes import settings_bp

    app.register_blueprint(auth_bp,      url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(customer_bp,  url_prefix='/customers')
    app.register_blueprint(billing_bp,   url_prefix='/billing')
    app.register_blueprint(sales_bp,     url_prefix='/sales')
    app.register_blueprint(employee_bp,  url_prefix='/employees')
    app.register_blueprint(ai_bp,        url_prefix='/ai')
    app.register_blueprint(api_bp)
    app.register_blueprint(settings_bp)

    # Register teardown context
    from database.models import close_db
    app.teardown_appcontext(close_db)

    # Make error template dir configurable
    app.config['ERROR_TEMPLATE_DIR'] = 'errors/'

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    # Jinja2 globals
    import datetime
    from utils.image_helpers import get_jewellery_image_path
    app.jinja_env.globals['now'] = datetime.datetime.utcnow
    app.jinja_env.globals['datetime'] = datetime.datetime
    app.jinja_env.globals['get_jewellery_image_path'] = get_jewellery_image_path

    return app
