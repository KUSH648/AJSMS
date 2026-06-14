"""
modules/employees.py
====================
Employee records, attendance marking, and salary management.
"""

from datetime import date
from database.models import (
    get_all_employees, get_employee_by_id, add_employee,
    update_employee, deactivate_employee,
    mark_attendance, get_attendance,
    add_salary_record, get_salary_records, pay_salary, query
)
from modules.auth import hash_password


def get_attendance_summary(emp_id, month_year=None):
    """Return present/absent/half-day counts for an employee."""
    if not month_year:
        month_year = date.today().strftime('%Y-%m')
    rows = get_attendance(emp_id, month_year)
    summary = {'Present': 0, 'Absent': 0, 'Half-Day': 0, 'Leave': 0}
    for r in rows:
        s = r.get('status', 'Absent')
        summary[s] = summary.get(s, 0) + 1
    summary['total_days'] = len(rows)
    return summary


def register_employee(form_data):
    """Validate and create a new employee. Returns (emp_id, error)."""
    name  = form_data.get('name', '').strip()
    email = form_data.get('email', '').strip()
    pwd   = form_data.get('password', '').strip()
    role  = form_data.get('role', 'Staff')

    if not name:
        return None, 'Name is required.'
    if not email:
        return None, 'Email is required.'
    if len(pwd) < 6:
        return None, 'Password must be at least 6 characters.'

    existing = query("SELECT employee_id FROM employees WHERE email=?", (email,), one=True)
    if existing:
        return None, f'Email {email} is already registered.'

    try:
        salary = float(form_data.get('salary', 0))
    except ValueError:
        salary = 0.0

    data = {
        'name':      name,
        'phone':     form_data.get('phone', ''),
        'email':     email,
        'address':   form_data.get('address', ''),
        'role':      role,
        'salary':    salary,
        'join_date': form_data.get('join_date', date.today().isoformat()),
    }
    pw_hash = hash_password(pwd)
    emp_id  = add_employee(data, pw_hash)
    return emp_id, None


def record_attendance_bulk(work_date, records):
    """
    Mark attendance for multiple employees.
    records: list of {'employee_id', 'check_in', 'check_out', 'status', 'notes'}
    """
    for r in records:
        mark_attendance(
            r['employee_id'],
            work_date,
            r.get('check_in', ''),
            r.get('check_out', ''),
            r.get('status', 'Present'),
            r.get('notes', ''),
        )


def generate_salary_slip(emp_id, month_year, bonus=0.0, deductions=0.0):
    """
    Create a salary record for the given month.
    Returns the record_id.
    """
    emp = get_employee_by_id(emp_id)
    if not emp:
        return None, 'Employee not found.'
    base   = emp['salary']
    rec_id = add_salary_record(emp_id, month_year, base, bonus, deductions)
    return rec_id, None


def get_payroll_summary(month_year=None):
    """Return payroll totals for a month."""
    if not month_year:
        month_year = date.today().strftime('%Y-%m')
    rows = query("""
        SELECT e.name, e.role, sr.*
        FROM salary_records sr
        JOIN employees e ON sr.employee_id = e.employee_id
        WHERE sr.month_year = ?
        ORDER BY e.name
    """, (month_year,))
    total_net = sum(r['net_salary'] for r in rows)
    return rows, total_net


def calculate_salaries(employees, month, year):
    """Calculate monthly salaries based on employee attendance."""
    month_year = f"{year}-{int(month):02d}"
    salary_data = []
    
    for emp in employees:
        emp_id = emp['employee_id']
        attendance = get_attendance_summary(emp_id, month_year)
        base_salary = emp.get('salary', 0.0) or 0.0
        
        present_days = attendance.get('Present', 0)
        absent_days = attendance.get('Absent', 0)
        half_days = attendance.get('Half-Day', 0)
        leave_days = attendance.get('Leave', 0)
        
        # Deduct salary for absent (1 day) and half-day (0.5 day)
        daily_rate = base_salary / 30.0 if base_salary > 0 else 0.0
        deductions = daily_rate * (absent_days + 0.5 * half_days)
        
        # We can query if there's any recorded bonus or custom deductions in the salary_records DB table
        # Let's search if they already have a salary record for this month
        bonus = 0.0
        custom_deductions = 0.0
        
        db_rec = query(
            "SELECT bonus, deductions FROM salary_records WHERE employee_id = ? AND month_year = ?",
            (emp_id, month_year), one=True
        )
        if db_rec:
            bonus = db_rec.get('bonus', 0.0) or 0.0
            custom_deductions = db_rec.get('deductions', 0.0) or 0.0
            
        total_deductions = deductions + custom_deductions
        net_salary = max(0.0, base_salary + bonus - total_deductions)
        
        salary_data.append({
            'employee_id': emp_id,
            'name': emp['name'],
            'role': emp['role'],
            'base_salary': base_salary,
            'present_days': present_days,
            'absent_days': absent_days,
            'half_days': half_days,
            'leave_days': leave_days,
            'deductions': round(total_deductions, 2),
            'bonus': round(bonus, 2),
            'net_salary': round(net_salary, 2),
            'month_year': month_year
        })
    return salary_data


def generate_payslip_pdf(emp, month, year):
    """Generate a beautiful PDF payslip using ReportLab."""
    import os
    os.makedirs('static/bills', exist_ok=True)
    filename = f"payslip_{emp['employee_id']}_{month}_{year}.pdf"
    filepath = os.path.join('static', 'bills', filename)
    rel_path = f"/static/bills/{filename}"
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
        REPORTLAB_AVAILABLE = True
    except ImportError:
        REPORTLAB_AVAILABLE = False
        
    if not REPORTLAB_AVAILABLE:
        # Fallback to plain text files if ReportLab is missing
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"========================================\n")
            f.write(f"             SALARY PAYSLIP             \n")
            f.write(f"========================================\n")
            f.write(f"Employee Name : {emp.get('name', '')}\n")
            f.write(f"Role          : {emp.get('role', '')}\n")
            f.write(f"Period        : {month}/{year}\n")
            f.write(f"----------------------------------------\n")
            f.write(f"Base Salary   : INR {emp.get('base_salary', 0.0):,.2f}\n")
            f.write(f"Bonus         : INR {emp.get('bonus', 0.0):,.2f}\n")
            f.write(f"Deductions    : INR {emp.get('deductions', 0.0):,.2f}\n")
            f.write(f"----------------------------------------\n")
            f.write(f"Net Salary    : INR {emp.get('net_salary', 0.0):,.2f}\n")
            f.write(f"========================================\n")
        return rel_path

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm,
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Gold accent colors
    GOLD = colors.HexColor('#B8860B')
    DARK = colors.HexColor('#1A1A2E')
    
    # Title Header
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=GOLD,
        alignment=TA_CENTER
    )
    
    story.append(Paragraph("💎 JEWELLERY SHOP MANAGEMENT SYSTEM", header_style))
    story.append(Spacer(1, 2*mm))
    
    sub_style = ParagraphStyle(
        'SubStyle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.gray
    )
    story.append(Paragraph("Employee Monthly Payslip", sub_style))
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width='100%', thickness=1, color=GOLD))
    story.append(Spacer(1, 5*mm))
    
    # Employee info
    info_data = [
        [Paragraph(f"<b>Employee Name:</b> {emp.get('name')}", styles['Normal']),
         Paragraph(f"<b>Role:</b> {emp.get('role')}", styles['Normal'])],
        [Paragraph(f"<b>Month/Year:</b> {month}/{year}", styles['Normal']),
         Paragraph(f"<b>Employee ID:</b> {emp.get('employee_id')}", styles['Normal'])]
    ]
    info_table = Table(info_data, colWidths=[90*mm, 90*mm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 8*mm))
    
    # Salary breakdown table
    salary_headers = [Paragraph("<b>Earnings / Deductions</b>", styles['Normal']), Paragraph("<b>Amount (INR)</b>", styles['Normal'])]
    salary_rows = [
        salary_headers,
        [Paragraph("Base Salary", styles['Normal']), Paragraph(f"{emp.get('base_salary', 0.0):,.2f}", styles['Normal'])],
        [Paragraph("Attendance Bonus / Other Incentives", styles['Normal']), Paragraph(f"{emp.get('bonus', 0.0):,.2f}", styles['Normal'])],
        [Paragraph("Attendance Deductions (Absences/Half days)", styles['Normal']), Paragraph(f"- {emp.get('deductions', 0.0):,.2f}", styles['Normal'])],
        [Paragraph("<b>Net Salary Paid</b>", styles['Normal']), Paragraph(f"<b>{emp.get('net_salary', 0.0):,.2f}</b>", styles['Normal'])]
    ]
    
    salary_table = Table(salary_rows, colWidths=[120*mm, 60*mm])
    salary_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F5F5F5')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#FFF8DC')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(salary_table)
    story.append(Spacer(1, 15*mm))
    
    # Footer signature
    sig_data = [
        ["", ""],
        ["_________________________", "_________________________"],
        ["Employee Signature", "Authorized Signatory"]
    ]
    sig_table = Table(sig_data, colWidths=[90*mm, 90*mm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(sig_table)
    
    doc.build(story)
    return rel_path

