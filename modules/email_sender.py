import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from config import Config


def _get_smtp_config():
    try:
        from database.models import get_setting
        server   = get_setting('mail_server')   or Config.MAIL_SERVER
        port_str = get_setting('mail_port')      or str(Config.MAIL_PORT)
        username = get_setting('mail_username')  or Config.MAIL_USERNAME
        password = get_setting('mail_password')  or Config.MAIL_PASSWORD
        return server, int(port_str), username, password
    except Exception:
        return (Config.MAIL_SERVER, Config.MAIL_PORT,
                Config.MAIL_USERNAME, Config.MAIL_PASSWORD)


def is_mail_configured():
    _, _, username, password = _get_smtp_config()
    return bool(username and password)


def send_invoice_email(to_email, bill, pdf_path):
    if not to_email:
        print("No recipient email provided.")
        return False

    server_addr, port, username, password = _get_smtp_config()

    if not username or not password:
        print(f"[MAIL MOCK] Mail not configured. Would send invoice email to {to_email} for bill {bill.get('bill_number')}")
        print(f"[MAIL MOCK] Attachment path: {pdf_path}")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = to_email
        msg['Subject'] = f"Invoice {bill.get('bill_number', '')} from {Config.SHOP_NAME}"

        body = (
            f"Dear {bill.get('customer_name', 'Valued Customer')},\n\n"
            f"Thank you for shopping with us!\n"
            f"Please find attached your invoice details.\n\n"
            f"Bill Number: {bill.get('bill_number', '')}\n"
            f"Total Amount: INR {bill.get('total_amount', 0.0):,.2f}\n"
            f"Date: {bill.get('bill_date', '')}\n\n"
            f"Best regards,\n"
            f"{Config.SHOP_NAME}"
        )
        msg.attach(MIMEText(body, 'plain'))

        if pdf_path and os.path.exists(pdf_path):
            filename = os.path.basename(pdf_path)
            with open(pdf_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename= {filename}")
                msg.attach(part)

        server = smtplib.SMTP(server_addr, port)
        server.starttls()
        server.login(username, password)
        server.sendmail(username, to_email, msg.as_string())
        server.quit()
        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")
        return False
