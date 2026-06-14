"""
utils/pdf_generator.py
=======================
Generates a professional GST invoice PDF using ReportLab.
"""

import os
from datetime import datetime
from flask import current_app

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph,
        Spacer, HRFlowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


GOLD = colors.HexColor('#B8860B')
DARK = colors.HexColor('#1A1A2E')
LIGHT_GOLD = colors.HexColor('#FFF8DC')


def generate_invoice_pdf(bill, sale_items, shop_cfg):
    """
    Generate a PDF invoice.

    Parameters
    ----------
    bill      : dict  – Bill row from DB (includes customer details)
    sale_items: list  – List of sale-item dicts
    shop_cfg  : dict  – {'name','address','phone','email','gstin','pan'}

    Returns
    -------
    str  – relative path to the saved PDF, e.g. 'static/bills/BILL-00001.pdf'
    """
    if not REPORTLAB_AVAILABLE:
        return _text_fallback(bill, sale_items, shop_cfg)

    os.makedirs('static/bills', exist_ok=True)
    bill_no  = bill.get('bill_number', 'BILL-00000')
    filename = f"static/bills/{bill_no}.pdf"

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm,   bottomMargin=15*mm,
    )

    styles = getSampleStyleSheet()
    story  = []

    # ── Header ──────────────────────────────────────────────────────
    header_data = [[
        Paragraph(f"<b><font size=18 color='#B8860B'>{shop_cfg['name']}</font></b>", styles['Normal']),
        Paragraph(
            f"<b><font size=14>TAX INVOICE</font></b><br/>"
            f"<font size=9 color='grey'>Bill No: {bill_no}</font>",
            ParagraphStyle('right', parent=styles['Normal'], alignment=TA_RIGHT)
        ),
    ]]
    header_tbl = Table(header_data, colWidths=[100*mm, 80*mm])
    header_tbl.setStyle(TableStyle([
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
    ]))
    story.append(header_tbl)

    # Shop details
    shop_detail = (
        f"{shop_cfg['address']}<br/>"
        f"Phone: {shop_cfg['phone']} | Email: {shop_cfg['email']}<br/>"
        f"GSTIN: {shop_cfg['gstin']} | PAN: {shop_cfg['pan']}"
    )
    story.append(Paragraph(
        f"<font size=8 color='grey'>{shop_detail}</font>",
        styles['Normal']
    ))
    story.append(HRFlowable(width='100%', thickness=1, color=GOLD))
    story.append(Spacer(1, 4*mm))

    # ── Bill details + Customer ──────────────────────────────────────
    bill_date = bill.get('bill_date', datetime.now().strftime('%Y-%m-%d %H:%M'))
    cust_info = (
        f"<b>Bill To:</b><br/>"
        f"{bill.get('customer_name','Walk-in Customer')}<br/>"
        f"{bill.get('customer_phone','')}<br/>"
        f"{bill.get('customer_address','') or ''}"
    )
    right_info = (
        f"<b>Date:</b> {str(bill_date)[:16]}<br/>"
        f"<b>Bill No:</b> {bill_no}<br/>"
        f"<b>Payment:</b> {bill.get('payment_method','Cash')}"
    )
    bi_data = [[
        Paragraph(cust_info, styles['Normal']),
        Paragraph(right_info, ParagraphStyle('right', parent=styles['Normal'], alignment=TA_RIGHT)),
    ]]
    bi_tbl = Table(bi_data, colWidths=[100*mm, 80*mm])
    bi_tbl.setStyle(TableStyle([('TOPPADDING', (0,0), (-1,-1), 2)]))
    story.append(bi_tbl)
    story.append(Spacer(1, 5*mm))

    # ── Item table ───────────────────────────────────────────────────
    item_headers = ['#', 'Item Description', 'Category', 'Qty', 'Unit Price (₹)', 'Total (₹)']
    item_rows = [item_headers]
    for idx, si in enumerate(sale_items, 1):
        item_rows.append([
            str(idx),
            si.get('item_name', ''),
            si.get('category', ''),
            str(si.get('quantity', 1)),
            f"{si.get('unit_price', 0):,.2f}",
            f"{si.get('total_price', 0):,.2f}",
        ])

    col_w = [8*mm, 65*mm, 25*mm, 12*mm, 28*mm, 25*mm]
    item_tbl = Table(item_rows, colWidths=col_w, repeatRows=1)
    item_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0), DARK),
        ('TEXTCOLOR',     (0,0), (-1,0), colors.white),
        ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, LIGHT_GOLD]),
        ('GRID',          (0,0), (-1,-1), 0.3, colors.lightgrey),
        ('ALIGN',         (3,0), (-1,-1), 'RIGHT'),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(item_tbl)
    story.append(Spacer(1, 4*mm))

    # ── Totals ───────────────────────────────────────────────────────
    sub    = bill.get('subtotal',    0)
    disc   = bill.get('discount',    0)
    cgst   = bill.get('cgst_amount', 0)
    sgst   = bill.get('sgst_amount', 0)
    total  = bill.get('total_amount',0)

    totals_data = [
        ['', 'Sub Total',  f"₹{sub:,.2f}"],
        ['', f'Discount',  f"-₹{disc:,.2f}"],
        ['', 'CGST (1.5%)',f"₹{cgst:,.2f}"],
        ['', 'SGST (1.5%)',f"₹{sgst:,.2f}"],
        ['', 'GRAND TOTAL',f"₹{total:,.2f}"],
    ]
    tot_tbl = Table(totals_data, colWidths=[120*mm, 35*mm, 28*mm])
    tot_tbl.setStyle(TableStyle([
        ('ALIGN',      (1,0), (-1,-1), 'RIGHT'),
        ('FONTNAME',   (0,4), (-1,4), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,4), (-1,4), 10),
        ('BACKGROUND', (0,4), (-1,4), DARK),
        ('TEXTCOLOR',  (0,4), (-1,4), GOLD),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(tot_tbl)

    # ── Footer ───────────────────────────────────────────────────────
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph(
        "<font size=8 color='grey'>Thank you for shopping at Shree Jewellers! "
        "All jewellery is certified and hallmarked. "
        "This is a computer-generated invoice — no signature required.</font>",
        ParagraphStyle('footer', parent=styles['Normal'], alignment=TA_CENTER)
    ))

    doc.build(story)
    return filename


def _text_fallback(bill, sale_items, shop_cfg):
    """Create a plain-text .txt invoice when ReportLab is not installed."""
    os.makedirs('static/bills', exist_ok=True)
    bill_no  = bill.get('bill_number', 'BILL-00000')
    filename = f"static/bills/{bill_no}.txt"

    lines = [
        shop_cfg['name'],
        shop_cfg['address'],
        f"Phone: {shop_cfg['phone']} | GSTIN: {shop_cfg['gstin']}",
        "=" * 60,
        f"TAX INVOICE - {bill_no}",
        f"Date: {str(bill.get('bill_date',''))[:16]}",
        f"Customer: {bill.get('customer_name','Walk-in')}",
        "-" * 60,
    ]
    for si in sale_items:
        lines.append(f"{si['item_name']}  x{si['quantity']}  ₹{si['total_price']:,.2f}")
    lines += [
        "-" * 60,
        f"Subtotal : ₹{bill.get('subtotal',0):,.2f}",
        f"Discount : -₹{bill.get('discount',0):,.2f}",
        f"GST (3%) : ₹{bill.get('gst_amount',0):,.2f}",
        f"TOTAL    : ₹{bill.get('total_amount',0):,.2f}",
        "=" * 60,
        "Thank you for shopping with us!",
    ]
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return filename
