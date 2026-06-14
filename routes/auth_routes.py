"""
Authentication Routes — login, logout, register, change-password
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
import sqlite3, hashlib, os
from config import Config

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# ── Decorators ────────────────────────────────────────────────────────────────
def admin_required(f):
    """Restrict endpoint to admin role only."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if getattr(current_user, 'role', '').lower() != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated


def staff_or_admin(f):
    """Allow staff and admin roles."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if getattr(current_user, 'role', '').lower() not in ('admin', 'manager', 'staff'):
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """Generic RBAC decorator — restricts to given role(s)."""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated(*args, **kwargs):
            if getattr(current_user, 'role', '').lower() not in [r.lower() for r in roles]:
                flash(f'Access denied. Requires one of: {", ".join(roles)}.', 'danger')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated
    return decorator



# ── Login / Logout ────────────────────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        remember = bool(request.form.get('remember'))

        if not username or not password:
            flash('Please enter both username and password.', 'warning')
            return render_template('login.html')

        try:
            from modules.auth import authenticate
            user = authenticate(username, password)
            if user:
                login_user(user, remember=remember)
                flash(f'Welcome back, {user.name}! 💎', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard.index'))
            else:
                flash('Invalid credentials. Please try again.', 'danger')
        except Exception as e:
            flash(f'Login error: {str(e)}', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    name = current_user.name if current_user.is_authenticated else ''
    logout_user()
    flash(f'Goodbye, {name}. See you soon!', 'info')
    return redirect(url_for('auth.login'))


# ── Change Password ───────────────────────────────────────────────────────────
@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_pwd  = request.form.get('current_password', '')
        new_pwd      = request.form.get('new_password', '')
        confirm_pwd  = request.form.get('confirm_password', '')

        if len(new_pwd) < 8:
            flash('New password must be at least 8 characters.', 'warning')
        elif new_pwd != confirm_pwd:
            flash('New passwords do not match.', 'danger')
        else:
            try:
                from modules.auth import change_user_password
                if change_user_password(current_user.id, current_pwd, new_pwd):
                    flash('Password changed successfully!', 'success')
                    return redirect(url_for('dashboard.index'))
                else:
                    flash('Current password is incorrect.', 'danger')
            except Exception as e:
                flash(f'Error: {str(e)}', 'danger')

    return render_template('auth/change_password.html')


# ── Register (admin only) ─────────────────────────────────────────────────────
@auth_bp.route('/register', methods=['GET', 'POST'])
@admin_required
def register():
    if request.method == 'POST':
        data = {
            'name':     request.form.get('name', '').strip(),
            'username': request.form.get('username', '').strip(),
            'password': request.form.get('password', ''),
            'role':     request.form.get('role', 'staff'),
            'email':    request.form.get('email', '').strip() or f'{request.form.get("username", "").strip()}@shop.com',
            'phone':    request.form.get('phone', '').strip(),
            'salary':   float(request.form.get('salary', 0) or 0),
            'join_date':request.form.get('join_date', ''),
        }

        if not all([data['name'], data['username'], data['password']]):
            flash('Name, username and password are required.', 'warning')
        elif len(data['password']) < 8:
            flash('Password must be at least 8 characters.', 'warning')
        else:
            try:
                from modules.employees import register_employee
                eid, err = register_employee(data)
                if eid:
                    flash(f'User "{data["name"]}" created successfully!', 'success')
                    return redirect(url_for('employee.list_employees'))
                else:
                    flash(f'Error: {err}', 'danger')
            except Exception as e:
                flash(f'Error creating user: {str(e)}', 'danger')

    return render_template('auth/register.html')


# ── Profile ───────────────────────────────────────────────────────────────────
@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', user=current_user)