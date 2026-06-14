from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from routes.auth_routes import admin_required

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

SETTING_KEYS = [
    'mail_server',
    'mail_port',
    'mail_use_tls',
    'mail_username',
    'mail_password',
    'shop_name',
    'shop_email',
]


@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
@admin_required
def index():
    from database.models import get_setting, set_setting, get_all_settings

    if request.method == 'POST':
        set_setting('mail_server',   request.form.get('mail_server', '').strip())
        set_setting('mail_port',     request.form.get('mail_port', '587').strip())
        set_setting('mail_username', request.form.get('mail_username', '').strip())
        pwd = request.form.get('mail_password', '').strip()
        if pwd:
            set_setting('mail_password', pwd)
        flash('SMTP settings saved successfully!', 'success')
        return redirect(url_for('settings.index'))

    all_settings = get_all_settings()
    return render_template('settings/index.html', settings=all_settings)
