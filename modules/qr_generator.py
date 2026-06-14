import os
import qrcode

def generate_bill_qr(bill_id, bill):
    bills_dir = os.path.join('static', 'bills')
    os.makedirs(bills_dir, exist_ok=True)
    
    qr_data = (
        f"Bill No: {bill.get('bill_number', '')}\n"
        f"Total: INR {bill.get('total_amount', 0.0)}\n"
        f"Date: {bill.get('bill_date', '')}"
    )
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    filename = f"qr_{bill_id}.png"
    filepath = os.path.join(bills_dir, filename)
    img.save(filepath)
    
    return f"/static/bills/{filename}"
