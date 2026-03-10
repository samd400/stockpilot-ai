"""Tax Report Service — generate tax summaries and exports."""

import csv
import io
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem

logger = logging.getLogger(__name__)


def generate_tax_summary(
    db: Session,
    tenant_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict:
    """Generate a tax summary for the tenant within the date range."""
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=90)

    invoices = db.query(Invoice).filter(
        Invoice.tenant_id == tenant_id,
        Invoice.created_at >= start_date,
        Invoice.created_at <= end_date,
    ).all()

    total_revenue = 0.0
    total_tax = 0.0
    total_cgst = 0.0
    total_sgst = 0.0
    invoice_count = len(invoices)
    currency = "INR"

    for inv in invoices:
        total_revenue += inv.total_amount or 0
        total_tax += inv.tax if hasattr(inv, 'tax') and inv.tax else 0
        currency = inv.currency if hasattr(inv, 'currency') and inv.currency else currency

    # Sum GST from invoice items
    items = db.query(
        func.coalesce(func.sum(InvoiceItem.cgst_amount), 0).label("cgst"),
        func.coalesce(func.sum(InvoiceItem.sgst_amount), 0).label("sgst"),
    ).join(Invoice, Invoice.id == InvoiceItem.invoice_id).filter(
        Invoice.tenant_id == tenant_id,
        Invoice.created_at >= start_date,
        Invoice.created_at <= end_date,
    ).first()

    total_cgst = float(items.cgst) if items else 0
    total_sgst = float(items.sgst) if items else 0

    return {
        "tenant_id": tenant_id,
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "invoice_count": invoice_count,
        "total_revenue": round(total_revenue, 2),
        "total_tax": round(total_tax, 2),
        "total_cgst": round(total_cgst, 2),
        "total_sgst": round(total_sgst, 2),
        "total_igst": round(total_tax - total_cgst - total_sgst, 2),
        "net_revenue": round(total_revenue - total_tax, 2),
        "currency": currency,
    }


def export_csv(summary: Dict) -> str:
    """Export tax summary as CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Metric", "Value"])
    for key, value in summary.items():
        if key == "period":
            writer.writerow(["Period Start", value["start"]])
            writer.writerow(["Period End", value["end"]])
        else:
            writer.writerow([key, value])
    return output.getvalue()


def export_pdf(summary: Dict) -> bytes:
    """Export tax summary as PDF. Returns plain text in PDF-like format (no dependency on reportlab)."""
    lines = [
        "=" * 50,
        "TAX SUMMARY REPORT",
        "=" * 50,
        f"Tenant: {summary.get('tenant_id', 'N/A')}",
        f"Period: {summary.get('period', {}).get('start', '')} to {summary.get('period', {}).get('end', '')}",
        "-" * 50,
        f"Invoice Count: {summary.get('invoice_count', 0)}",
        f"Total Revenue: {summary.get('currency', 'INR')} {summary.get('total_revenue', 0)}",
        f"Total Tax: {summary.get('currency', 'INR')} {summary.get('total_tax', 0)}",
        f"  CGST: {summary.get('total_cgst', 0)}",
        f"  SGST: {summary.get('total_sgst', 0)}",
        f"  IGST: {summary.get('total_igst', 0)}",
        f"Net Revenue: {summary.get('currency', 'INR')} {summary.get('net_revenue', 0)}",
        "=" * 50,
    ]
    return "\n".join(lines).encode("utf-8")
