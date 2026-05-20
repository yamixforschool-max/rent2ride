"""
Utility functions for PDF generation and email
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.conf import settings
from django.core.files.base import ContentFile
from io import BytesIO
import os


def generate_rental_agreement_pdf(agreement):
    """Generate PDF for rental agreement"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0D9488'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    title = Paragraph("RENTAL AGREEMENT", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.2*inch))
    
    # Contract Number
    contract_style = ParagraphStyle(
        'ContractNumber',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER
    )
    contract_num = Paragraph(f"Contract Number: {agreement.contract_number}", contract_style)
    elements.append(contract_num)
    elements.append(Spacer(1, 0.3*inch))
    
    # Agreement Details
    data = [
        ['Renter Information', ''],
        ['Name:', f"{agreement.booking.user.get_full_name() or agreement.booking.user.username}"],
        ['Email:', agreement.booking.user.email],
        ['', ''],
        ['Vehicle Owner Information', ''],
        ['Name:', f"{agreement.booking.vehicle.owner.get_full_name() or agreement.booking.vehicle.owner.username}"],
        ['Email:', agreement.booking.vehicle.owner.email],
        ['', ''],
        ['Vehicle Information', ''],
        ['Vehicle:', f"{agreement.booking.vehicle.brand} {agreement.booking.vehicle.model}"],
        ['Type:', agreement.booking.vehicle.get_vehicle_type_display()],
        ['Location:', agreement.booking.vehicle.location],
        ['', ''],
        ['Rental Period', ''],
        ['Start Date:', agreement.booking.start_date.strftime("%B %d, %Y at %I:%M %p")],
        ['End Date:', agreement.booking.end_date.strftime("%B %d, %Y at %I:%M %p")],
        ['', ''],
        ['Financial Terms', ''],
        ['Total Amount:', f"₱{agreement.booking.total_price:,.2f}"],
        ['Deposit Amount:', f"₱{agreement.booking.deposit_amount:,.2f}"],
        ['Insurance:', f"₱{agreement.booking.insurance_amount:,.2f}"],
    ]
    
    table = Table(data, colWidths=[2*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Terms and Conditions
    terms_style = ParagraphStyle(
        'Terms',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_LEFT,
        spaceAfter=12
    )
    terms_title = Paragraph("<b>Terms and Conditions:</b>", terms_style)
    elements.append(terms_title)
    
    terms_text = agreement.terms_and_conditions or """
    1. The renter is responsible for the vehicle during the rental period.
    2. Any damages to the vehicle will be charged to the renter.
    3. Late returns will incur penalties as specified.
    4. The vehicle must be returned in the same condition as received.
    5. All traffic violations are the renter's responsibility.
    6. The renter must have a valid driver's license.
    7. Insurance coverage is as specified in the booking.
    """
    
    terms_para = Paragraph(terms_text, terms_style)
    elements.append(terms_para)
    elements.append(Spacer(1, 0.3*inch))
    
    # Signatures
    signature_data = [
        ['Renter Signature', 'Owner Signature'],
        ['', ''],
        ['', ''],
        ['_________________________', '_________________________'],
        [f"{agreement.booking.user.get_full_name() or agreement.booking.user.username}", 
         f"{agreement.booking.vehicle.owner.get_full_name() or agreement.booking.vehicle.owner.username}"],
        [f"Date: {agreement.renter_signed_at.strftime('%B %d, %Y') if agreement.renter_signed_at else 'Not signed'}", 
         f"Date: {agreement.owner_signed_at.strftime('%B %d, %Y') if agreement.owner_signed_at else 'Not signed'}"],
    ]
    
    sig_table = Table(signature_data, colWidths=[3*inch, 3*inch])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(sig_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_invoice_pdf(invoice):
    """Generate PDF invoice for booking"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0D9488'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    title = Paragraph("INVOICE", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.2*inch))
    
    # Invoice Number
    invoice_style = ParagraphStyle(
        'InvoiceNumber',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER
    )
    invoice_num = Paragraph(f"Invoice #: {invoice.invoice_number}", invoice_style)
    elements.append(invoice_num)
    elements.append(Spacer(1, 0.3*inch))
    
    # Header Information
    header_data = [
        ['Bill To:', 'Invoice Details:'],
        [f"{invoice.booking.user.get_full_name() or invoice.booking.user.username}", 
         f"Date: {invoice.generated_at.strftime('%B %d, %Y')}"],
        [invoice.booking.user.email, f"Booking #: {invoice.booking.id}"],
    ]
    
    header_table = Table(header_data, colWidths=[3*inch, 3*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Vehicle Information
    vehicle_data = [
        ['Vehicle:', f"{invoice.booking.vehicle.brand} {invoice.booking.vehicle.model}"],
        ['Type:', invoice.booking.vehicle.get_vehicle_type_display()],
        ['Location:', invoice.booking.vehicle.location],
        ['Rental Period:', f"{invoice.booking.start_date.strftime('%B %d, %Y')} to {invoice.booking.end_date.strftime('%B %d, %Y')}"],
    ]
    
    vehicle_table = Table(vehicle_data, colWidths=[2*inch, 4*inch])
    vehicle_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(vehicle_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Items Table
    days = (invoice.booking.end_date - invoice.booking.start_date).days + 1
    rental_fee = invoice.booking.vehicle.price_per_day * days
    
    items_data = [
        ['Description', 'Quantity', 'Unit Price', 'Amount'],
        ['Rental Fee', f'{days} days', f'₱{invoice.booking.vehicle.price_per_day:,.2f}', f'₱{rental_fee:,.2f}'],
    ]
    
    if invoice.booking.insurance_amount > 0:
        items_data.append(['Insurance Coverage', f'{days} days', '₱500.00', f'₱{invoice.booking.insurance_amount:,.2f}'])
    
    if invoice.booking.discount_amount > 0:
        items_data.append(['Discount', '1', '-', f'-₱{invoice.booking.discount_amount:,.2f}'])
    
    if invoice.booking.late_penalty > 0:
        items_data.append(['Late Return Penalty', '1', '-', f'₱{invoice.booking.late_penalty:,.2f}'])
    
    items_table = Table(items_data, colWidths=[2.5*inch, 1*inch, 1.5*inch, 1*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Total
    total_data = [
        ['Subtotal:', f'₱{rental_fee + invoice.booking.insurance_amount:,.2f}'],
        ['Discount:', f'-₱{invoice.booking.discount_amount:,.2f}'],
        ['Late Penalty:', f'₱{invoice.booking.late_penalty:,.2f}'],
        ['TOTAL:', f'₱{invoice.booking.total_price:,.2f}'],
    ]
    
    total_table = Table(total_data, colWidths=[4*inch, 2*inch])
    total_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (-1, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('FONTSIZE', (-1, -1), (-1, -1), 14),
        ('TEXTCOLOR', (-1, -1), (-1, -1), colors.HexColor('#0D9488')),
        ('GRID', (0, -1), (-1, -1), 2, colors.black),
        ('BACKGROUND', (-1, -1), (-1, -1), colors.lightgrey),
    ]))
    elements.append(total_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Payment Status
    status_style = ParagraphStyle(
        'Status',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER
    )
    payment_status = "PAID" if invoice.booking.payment_status == 'paid' else "PENDING"
    status_text = Paragraph(f"<b>Payment Status: {payment_status}</b>", status_style)
    elements.append(status_text)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
