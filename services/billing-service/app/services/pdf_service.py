"""
Professional invoice PDF generation using ReportLab.
Supports India GST, GCC VAT, EU VAT layouts.
"""
import io
from datetime import datetime
from typing import List, Dict, Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph,
                                  Spacer, HRFlowable)
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER


def generate_invoice_pdf(invoice: Any, items: List[Any],
                          tenant_info: Optional[Dict] = None) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=15*mm, leftMargin=15*mm,
                             topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    story = []

    # ── Header ──────────────────────────────────────────────
    header_style = ParagraphStyle("header", fontSize=20, textColor=colors.HexColor("#1a1a2e"),
                                   spaceAfter=4, fontName="Helvetica-Bold")
    sub_style = ParagraphStyle("sub", fontSize=9, textColor=colors.grey, spaceAfter=2)
    right_style = ParagraphStyle("right", fontSize=9, alignment=TA_RIGHT)

    company_name = (tenant_info or {}).get("name", "StockPilot Business")
    gst_number = (tenant_info or {}).get("gst_number", "")
    address = (tenant_info or {}).get("business_address", "")

    header_data = [
        [Paragraph(company_name, header_style),
         Paragraph(f"<b>INVOICE</b>", ParagraphStyle("inv", fontSize=22, alignment=TA_RIGHT,
                                                      fontName="Helvetica-Bold",
                                                      textColor=colors.HexColor("#2d6a4f")))],
        [Paragraph(address or "", sub_style),
         Paragraph(f"# {getattr(invoice, 'invoice_number', 'N/A')}", right_style)],
        [Paragraph(f"GST: {gst_number}" if gst_number else "", sub_style),
         Paragraph(f"Date: {getattr(invoice, 'created_at', datetime.utcnow()).strftime('%d %b %Y')}", right_style)],
    ]
    header_table = Table(header_data, colWidths=[105*mm, 75*mm])
    header_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                       ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2d6a4f"), spaceAfter=6))

    # ── Bill To ──────────────────────────────────────────────
    bill_to_data = [
        [Paragraph("<b>Bill To:</b>", styles["Normal"]),
         Paragraph("<b>Payment Status:</b>", styles["Normal"])],
        [Paragraph(getattr(invoice, "customer_name", "Walk-in Customer") or "Walk-in Customer",
                   styles["Normal"]),
         Paragraph(getattr(invoice, "payment_status", "UNPAID"),
                   ParagraphStyle("status", fontSize=10, fontName="Helvetica-Bold",
                                  textColor=colors.green if getattr(invoice, "payment_status", "") == "PAID"
                                  else colors.red))],
        [Paragraph(getattr(invoice, "customer_phone", "") or "", sub_style),
         Paragraph(f"Currency: {getattr(invoice, 'currency', 'INR')}", sub_style)],
    ]
    bill_table = Table(bill_to_data, colWidths=[120*mm, 60*mm])
    bill_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                     ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    story.append(bill_table)
    story.append(Spacer(1, 6*mm))

    # ── Items Table ──────────────────────────────────────────
    region = getattr(invoice, "region", "india_gst")
    has_gst = region == "india_gst"
    has_vat = region in ("gcc_vat", "eu_vat")

    if has_gst:
        col_headers = ["#", "Product", "HSN", "Qty", "Unit Price", "GST%", "CGST", "SGST", "Total"]
        col_widths = [8*mm, 45*mm, 18*mm, 12*mm, 20*mm, 14*mm, 18*mm, 18*mm, 22*mm]
    elif has_vat:
        col_headers = ["#", "Product", "Qty", "Unit Price", "VAT%", "VAT Amt", "Total"]
        col_widths = [8*mm, 60*mm, 15*mm, 25*mm, 15*mm, 22*mm, 30*mm]
    else:
        col_headers = ["#", "Product", "Qty", "Unit Price", "Tax", "Total"]
        col_widths = [8*mm, 70*mm, 15*mm, 30*mm, 20*mm, 32*mm]

    table_data = [col_headers]
    for i, item in enumerate(items, 1):
        qty = getattr(item, "quantity", 1)
        price = getattr(item, "price_per_unit", 0)
        name = getattr(item, "product_name", "Product")

        if has_gst:
            gst_pct = getattr(item, "gst_percentage", 0) or 0
            cgst = getattr(item, "cgst_amount", 0) or 0
            sgst = getattr(item, "sgst_amount", 0) or 0
            line_total = price * qty + cgst + sgst
            row = [str(i), name, "", str(qty), f"{price:.2f}", f"{gst_pct}%",
                   f"{cgst:.2f}", f"{sgst:.2f}", f"{line_total:.2f}"]
        elif has_vat:
            vat = getattr(item, "vat_amount", 0) or 0
            line_total = price * qty + vat
            vat_pct = round(vat / (price * qty) * 100, 1) if price * qty > 0 else 0
            row = [str(i), name, str(qty), f"{price:.2f}", f"{vat_pct}%",
                   f"{vat:.2f}", f"{line_total:.2f}"]
        else:
            line_total = getattr(item, "line_total", price * qty)
            row = [str(i), name, str(qty), f"{price:.2f}", "0%", f"{line_total:.2f}"]
        table_data.append(row)

    items_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 4*mm))

    # ── Totals ───────────────────────────────────────────────
    currency = getattr(invoice, "currency", "INR")
    subtotal = getattr(invoice, "subtotal", 0) or 0
    gst_amount = getattr(invoice, "gst_amount", 0) or 0
    vat_amount = getattr(invoice, "vat_amount", 0) or 0
    total = getattr(invoice, "total_amount", 0) or 0
    amount_paid = getattr(invoice, "amount_paid", 0) or 0
    amount_due = getattr(invoice, "amount_due", total) or 0

    totals_data = [
        ["", "Subtotal:", f"{currency} {subtotal:.2f}"],
    ]
    if gst_amount:
        totals_data.append(["", "GST:", f"{currency} {gst_amount:.2f}"])
    if vat_amount:
        totals_data.append(["", "VAT:", f"{currency} {vat_amount:.2f}"])
    totals_data.append(["", "TOTAL:", f"{currency} {total:.2f}"])
    if amount_paid:
        totals_data.append(["", "Paid:", f"{currency} {amount_paid:.2f}"])
    if amount_due:
        totals_data.append(["", "Balance Due:", f"{currency} {amount_due:.2f}"])

    totals_table = Table(totals_data, colWidths=[100*mm, 40*mm, 40*mm])
    totals_table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (1, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEABOVE", (1, -1), (-1, -1), 1, colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(totals_table)

    # ── Notes ────────────────────────────────────────────────
    notes = getattr(invoice, "notes", None)
    if notes:
        story.append(Spacer(1, 6*mm))
        story.append(Paragraph(f"<b>Notes:</b> {notes}", sub_style))

    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Paragraph("Thank you for your business!",
                            ParagraphStyle("footer", fontSize=8, alignment=TA_CENTER, textColor=colors.grey)))

    doc.build(story)
    buffer.seek(0)
    return buffer
