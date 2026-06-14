"""
modules/auth.py
===============
Authentication logic: Flask-Login User wrapper, login, password hashing.
"""

import bcrypt
from flask_login import UserMixin
from database.models import get_employee_by_id as _get_emp, get_employee_by_email


class Employee(UserMixin):
    """Flask-Login user wrapper around an employee dict."""

    def __init__(self, emp_dict):
        self._data = emp_dict

    # Flask-Login requires get_id()
    def get_id(self):
        return str(self._data['employee_id'])

    # Convenience attributes
    @property
    def id(self):          return self._data['employee_id']
    @property
    def name(self):        return self._data['name']
    @property
    def email(self):       return self._data['email']
    @property
    def role(self):        return self._data['role']
    @property
    def is_active(self):   return bool(self._data.get('is_active', 1))
    @property
    def is_admin(self):    return self._data['role'] == 'Admin'
    @property
    def is_manager(self):  return self._data['role'] in ('Admin', 'Manager')


def get_employee_by_id(emp_id):
    """Used by Flask-Login's user_loader."""
    data = _get_emp(emp_id)
    return Employee(data) if data else None


def authenticate(username_or_email, password):
    """Return Employee if credentials match, else None.

    Tries matching by email first, then falls back to name
    (partial match) so users can log in with their email
    or any part of their display name.
    """
    from database.models import query as _q

    # 1. Try by email
    emp = get_employee_by_email(username_or_email)

    # 2. Fallback: try by name (any match, case-insensitive)
    if not emp:
        emp = _q(
            "SELECT * FROM employees WHERE LOWER(name) LIKE LOWER(?) AND is_active = 1",
            (f"%{username_or_email}%",), one=True
        )

    if emp and emp.get('is_active'):
        stored = emp['password_hash']
        if isinstance(stored, str):
            stored = stored.encode()
        if bcrypt.checkpw(password.encode(), stored):
            return Employee(emp)
    return None


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password, hashed):
    if isinstance(hashed, str):
        hashed = hashed.encode()
    return bcrypt.checkpw(password.encode(), hashed)


def change_user_password(user_id, current_password, new_password):
    from database.models import get_employee_by_id, execute
    emp = get_employee_by_id(user_id)
    if emp:
        stored = emp['password_hash']
        if isinstance(stored, str):
            stored = stored.encode()
        if bcrypt.checkpw(current_password.encode(), stored):
            new_hash = hash_password(new_password)
            execute("UPDATE employees SET password_hash = ? WHERE employee_id = ?", (new_hash, user_id))
            return True
    return False


def create_user(data):
    """Create a new user via register_employee.

    register_employee returns (emp_id, error).  We return emp_id on
    success or None when there is an error.
    """
    from modules.employees import register_employee
    result = register_employee(data)
    if isinstance(result, tuple):
        emp_id, error = result
        if error:
            return None
        return emp_id
    return result

