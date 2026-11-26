import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_receipt_pdf(
    receipt_code: str,
    store_name: str = "FreshScan Partner Store",
    items: list = None,
    subtotal: float = 0.0,
    tax: float = 0.0,
    total: float = 0.0,
    currency_symbol: str = "$",
    created_at: str = None,
) -> bytes:
    """
    Generates a high-quality PDF receipt for a FreshScan order.
    """
    if items is None:
        items = []

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'ReceiptTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#064E3B'),
        alignment=1,
    )

    tagline_style = ParagraphStyle(
        'ReceiptTagline',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#10B981'),
        alignment=1,
    )

    meta_style = ParagraphStyle(
        'ReceiptMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748B'),
    )

    meta_right = ParagraphStyle(
        'ReceiptMetaRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748B'),
        alignment=2,
    )

    date_str = created_at or datetime.now().strftime("%b %d, %Y · %I:%M %p")

    elements = [
        Spacer(1, 10),
        Paragraph('FreshScan', title_style),
        Paragraph('OFFICIAL DIGITAL GROCERY RECEIPT · AI VERIFIED', tagline_style),
        Spacer(1, 15),
        HRFlowable(width='100%', thickness=2, color=colors.HexColor('#10B981')),
        Spacer(1, 12),
    ]

    # Meta Table: Store info on left, Receipt Code and Date on right
    meta_data = [
        [
            Paragraph(f"<b>Store:</b> {store_name}<br/><b>Status:</b> Completed (Paid)<br/><b>Checkout:</b> Smart Scan YOLO11", meta_style),
            Paragraph(f"<b>Receipt Code:</b> {receipt_code}<br/><b>Date:</b> {date_str}<br/><b>Payment:</b> Verified", meta_right),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[280, 250])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 14))

    # Items Table
    table_rows = [
        ['Item Description', 'Qty / Weight', 'Unit Price', 'Amount']
    ]

    if items and len(items) > 0:
        for it in items:
            name = it.get('name') or it.get('item_name') or 'Grocery Item'
            qty = it.get('quantity', 1)
            weight = it.get('weight')
            unit_price = it.get('unitPrice') or it.get('unit_price') or 0.0
            total_price = it.get('totalPrice') or it.get('total_price') or (unit_price * qty)

            qty_display = f"{weight:.3f} kg" if weight else f"{qty}x"
            unit_str = f"{currency_symbol}{unit_price:.2f}"
            amount_str = f"{currency_symbol}{total_price:.2f}"

            table_rows.append([name, qty_display, unit_str, amount_str])
    else:
        table_rows.append(['Grocery items scanned', '1 trip', f"{currency_symbol}{subtotal:.2f}", f"{currency_symbol}{subtotal:.2f}"])

    item_table = Table(table_rows, colWidths=[240, 95, 95, 100])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor('#CBD5E1')),
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 14))

    # Totals breakdown
    summary_data = [
        ['', 'Subtotal:', f"{currency_symbol}{subtotal:.2f}"],
        ['', 'Tax (Standard):', f"{currency_symbol}{tax:.2f}"],
        ['', 'Total Charged:', f"{currency_symbol}{total:.2f}"],
    ]
    summary_table = Table(summary_data, colWidths=[290, 140, 100])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 0), (-1, 1), 9.5),
        ('FONTSIZE', (1, 2), (-1, 2), 12),
        ('TEXTCOLOR', (1, 2), (-1, 2), colors.HexColor('#064E3B')),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LINEABOVE', (1, 2), (-1, 2), 1.5, colors.HexColor('#10B981')),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 25))

    # Verification note & Footer
    footer_style = ParagraphStyle(
        'ReceiptFooter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#94A3B8'),
        alignment=1,
    )
    elements.append(HRFlowable(width='100%', thickness=0.8, color=colors.HexColor('#E2E8F0')))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(f"Thank you for shopping with FreshScan · Freshness & Quality Verified · Receipt #{receipt_code}", footer_style))
    elements.append(Paragraph("Keep this receipt for returns or customer support. Scan code at exit kiosk.", footer_style))

    doc.build(elements)
    return buf.getvalue()
