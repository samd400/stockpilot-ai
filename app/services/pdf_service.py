from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from io import BytesIO
from datetime import datetime


def number_to_words(n):
    # Simple version (can improve later)
    return f"{int(n):,} Rupees Only"


def generate_invoice_pdf(invoice, items):

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # =============================
    # HEADER - SELLER DETAILS
    # =============================
    elements.append(Paragraph("<b>StockPilot</b>", styles["Title"]))
    elements.append(Paragraph("Address: Bangalore, India", styles["Normal"]))
    elements.append(Paragraph("GSTIN: 29ABCDE1234F2Z5", styles["Normal"]))
    elements.append(Paragraph("Phone: +91 9876543210", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # =============================
    # INVOICE DETAILS
    # =============================
    elements.append(Paragraph(f"<b>Invoice No:</b> {invoice.invoice_number}", styles["Normal"]))

    elements.append(Paragraph(f"<b>Date:</b> {invoice.created_at.strftime('%d-%m-%Y')}", styles["Normal"]))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(f"<b>Bill To:</b> {invoice.customer_name}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Phone:</b> {invoice.customer_phone}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # =============================
    # ITEM TABLE
    # =============================
    data = [["Product", "HSN", "Qty", "Rate", "Taxable", "CGST", "SGST", "Total"]]

    total_taxable = 0
    total_cgst = 0
    total_sgst = 0

    for item in items:
        taxable = item.quantity * item.price_per_unit
        cgst = item.cgst_amount or 0
        sgst = item.sgst_amount or 0
        total_line = taxable + cgst + sgst

        total_taxable += taxable
        total_cgst += cgst
        total_sgst += sgst

        data.append([
            item.product.product_name,
            item.product.hsn_code or "-",
            item.quantity,
            f"{item.price_per_unit:.2f}",
            f"{taxable:.2f}",
            f"{cgst:.2f}",
            f"{sgst:.2f}",
            f"{total_line:.2f}"
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (2, 1), (-1, -1), "CENTER"),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # =============================
    # TAX SUMMARY
    # =============================
    summary_data = [
        ["Total Taxable Value", f"{total_taxable:.2f}"],
        ["Total CGST", f"{total_cgst:.2f}"],
        ["Total SGST", f"{total_sgst:.2f}"],
        ["Grand Total", f"{invoice.total_amount:.2f}"]
    ]

    summary_table = Table(summary_data, colWidths=[300, 100])
    summary_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, -1), (-1, -1), colors.whitesmoke),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # =============================
    # AMOUNT IN WORDS
    # =============================
    elements.append(Paragraph(
        f"<b>Amount in Words:</b> {number_to_words(invoice.total_amount)}",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 40))

    # =============================
    # FOOTER
    # =============================
    elements.append(Paragraph("Authorized Signature", styles["Normal"]))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        "This is a computer generated invoice. No signature required.",
        styles["Normal"]
    ))

    doc.build(elements)
    buffer.seek(0)

    return buffer
