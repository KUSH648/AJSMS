"""
Employee Routes — CRUD, attendance, salary management, payslip PDF
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from routes.auth_routes import admin_required, role_required
from datetime import date, datetime
import os

employee_bp = Blueprint('employee', __name__, url_prefix='/employees')

ROLES = ['Admin', 'Manager', 'Staff', 'Cashier', 'Salesperson']


# ── List employees ────────────────────────────────────────────────────────────
@employee_bp.route('/')
@role_required('admin', 'manager')
def list_employees():
    from database.models import get_all_employees
    search = request.args.get('q', '').strip()
    role   = request.args.get('role', '')
    employees = get_all_employees(search=search, role=role)
    return render_template('employees/list.html', employees=employees,
                           search=search, selected_role=role, roles=ROLES)


# ── Add employee ──────────────────────────────────────────────────────────────
@employee_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add_employee():
    if request.method == 'POST':
        data = {
            'name':      request.form.get('name', '').strip(),
            'role':      request.form.get('role', 'Staff'),
            'phone':     request.form.get('phone', '').strip(),
            'email':     request.form.get('email', '').strip(),
            'address':   request.form.get('address', '').strip(),
            'salary':    float(request.form.get('salary', 0) or 0),
            'join_date': request.form.get('join_date', str(date.today())),
            'aadhar':    request.form.get('aadhar', '').strip(),
            'pan':       request.form.get('pan', '').strip(),
            'username':  request.form.get('username', '').strip(),
            'password':  request.form.get('password', ''),
        }
        if not data['name']:
            flash('Employee name is required.', 'warning')
        elif not data['username']:
            flash('Username is required for login.', 'warning')
        else:
            try:
                from modules.employees import register_employee as do_add
                eid, err = do_add(data)
                if err:
                    flash(f'Error: {err}', 'danger')
                else:
                    flash(f'Employee "{data["name"]}" added successfully!', 'success')
                    return redirect(url_for('employee.list_employees'))
            except Exception as e:
                flash(f'Error: {str(e)}', 'danger')

    return render_template('employees/add.html', roles=ROLES,
                           today=str(date.today()))


# ── Edit employee ─────────────────────────────────────────────────────────────
@employee_bp.route('/edit/<int:emp_id>', methods=['GET', 'POST'])
@admin_required
def edit_employee(emp_id):
    from database.models import get_employee_by_id, update_employee
    emp = get_employee_by_id(emp_id)
    if not emp:
        flash('Employee not found.', 'danger')
        return redirect(url_for('employee.list_employees'))

    if request.method == 'POST':
        data = {
            'name':    request.form.get('name', '').strip(),
            'role':    request.form.get('role', 'Staff'),
            'phone':   request.form.get('phone', '').strip(),
            'email':   request.form.get('email', '').strip(),
            'address': request.form.get('address', '').strip(),
            'salary':  float(request.form.get('salary', 0) or 0),
            'aadhar':  request.form.get('aadhar', '').strip(),
            'pan':     request.form.get('pan', '').strip(),
        }
        try:
            update_employee(emp_id, data)
            flash('Employee updated!', 'success')
            return redirect(url_for('employee.list_employees'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    return render_template('employees/edit.html', emp=emp, roles=ROLES)


# ── Delete employee ───────────────────────────────────────────────────────────
@employee_bp.route('/delete/<int:emp_id>', methods=['POST'])
@admin_required
def delete_employee(emp_id):
    if emp_id == current_user.id:
        flash("You can't delete yourself.", 'warning')
        return redirect(url_for('employee.list_employees'))
    try:
        from database.models import delete_employee
        delete_employee(emp_id)
        flash('Employee record deleted.', 'info')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('employee.list_employees'))


# ── Attendance ────────────────────────────────────────────────────────────────
@employee_bp.route('/attendance', methods=['GET', 'POST'])
@role_required('admin', 'manager')
def attendance():
    from database.models import get_all_employees, get_attendance_for_date, save_attendance
    today     = str(date.today())
    att_date  = request.args.get('date', today)

    if request.method == 'POST':
        att_date = request.form.get('att_date', today)
        records  = {}
        for key, val in request.form.items():
            if key.startswith('att_') and key != 'att_date':
                parts = key.split('_')
                if len(parts) == 2 and parts[1].isdigit():
                    eid = int(parts[1])
                    records[eid] = val
        try:
            save_attendance(att_date, records)
            flash(f'Attendance saved for {att_date}.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('employee.attendance', date=att_date))

    employees   = get_all_employees(only_active=True)
    att_records = get_attendance_for_date(att_date)  # {emp_id: status}

    return render_template('employees/attendance.html',
                           employees=employees, att_records=att_records,
                           att_date=att_date, today=today)


# ── Salary adjustment (admin only) ──────────────────────────────────────────
@employee_bp.route('/salary/adjust', methods=['POST'])
@admin_required
def adjust_salary():
    emp_id = int(request.form.get('emp_id', 0))
    month  = int(request.form.get('month', date.today().month))
    year   = int(request.form.get('year', date.today().year))
    bonus  = float(request.form.get('bonus', 0) or 0)
    deductions = float(request.form.get('deductions', 0) or 0)
    month_year = f"{year}-{int(month):02d}"
    try:
        from database.models import add_salary_record
        from database.models import get_employee_by_id
        emp = get_employee_by_id(emp_id)
        if not emp:
            flash('Employee not found.', 'danger')
        else:
            add_salary_record(emp_id, month_year, emp.get('salary', 0), bonus, deductions)
            flash(f'Salary adjusted for {emp["name"]}!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('employee.salary', month=month, year=year))


# ── Salary management ─────────────────────────────────────────────────────────
@employee_bp.route('/salary')
@admin_required
def salary():
    from database.models import get_all_employees
    from modules.employees import calculate_salaries
    month = int(request.args.get('month', date.today().month))
    year  = int(request.args.get('year',  date.today().year))
    employees = get_all_employees(only_active=True)
    salary_data = calculate_salaries(employees, month, year)
    salary_data = [s for s in salary_data if s['role'].lower() != 'admin']
    return render_template('employees/salary.html',
                           salary_data=salary_data, month=month, year=year,
                           months=list(range(1, 13)),
                           years=list(range(date.today().year - 2, date.today().year + 1)),
                           current_user=current_user)


# ── Generate payslip PDF ──────────────────────────────────────────────────────
@employee_bp.route('/payslip/<int:emp_id>')
@login_required
def payslip(emp_id):
    from database.models import get_employee_by_id
    from modules.employees import generate_payslip_pdf, calculate_salaries
    emp   = get_employee_by_id(emp_id)
    month = int(request.args.get('month', date.today().month))
    year  = int(request.args.get('year',  date.today().year))
    if not emp:
        flash('Employee not found.', 'danger')
        return redirect(url_for('employee.list_employees'))
        
    # Calculate detailed salary breakdown first
    salary_data = calculate_salaries([emp], month, year)
    emp_salary = salary_data[0]
    
    filepath = generate_payslip_pdf(emp_salary, month, year)
    return send_file(os.path.join(os.getcwd(), filepath.lstrip('/')), as_attachment=True,
                     download_name=f'payslip_{emp["name"]}_{month}_{year}.pdf')


# ── Attendance report export ──────────────────────────────────────────────────
@employee_bp.route('/attendance/export')
@login_required
def export_attendance():
    try:
        from database.models import get_attendance_in_range
        from modules.excel_export import export_attendance_to_excel
        date_from = request.args.get('from', str(date.today()))
        date_to   = request.args.get('to',   str(date.today()))
        data      = get_attendance_in_range(date_from, date_to)
        filepath  = export_attendance_to_excel(data, date_from, date_to)
        return send_file(filepath, as_attachment=True,
                         download_name=f'attendance_{date_from}_{date_to}.xlsx',
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        flash(f'Export error: {str(e)}', 'danger')
        return redirect(url_for('employee.attendance'))