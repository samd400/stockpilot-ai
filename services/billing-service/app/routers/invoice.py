"""
Billing Service — Invoice Router
Handles invoice creation with cross-service calls for stock deduction and customer info.
"""
import os
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import httpx

from app.core.database import get_db
from app.core.deps import get_current_user, require_billing_role, require_any_role
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.services.tax_engine import tax_engine
from app.services.invoice_number_service import generate_invoice_number
from app.services.pdf_service import generate_invoice_pdf

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/invoices", tags=["Invoices"])

INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://inventory-service:8002")
CRM_SERVICE_URL = os.getenv("CRM_SERVICE_URL", "http://crm-service:8004")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8006")
SERVICE_TOKEN = os.getenv("SERVICE_TOKEN", "internal-service-secret-change-me")
SERVICE_HEADERS = {"X-Service-Token": SERVICE_TOKEN, "Content-Type": "application/json"}


async def _deduct_stock(tenant_id: str, items: List[Dict]) -> bool:
    """Call inventory-service to deduct stock."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{INVENTORY_SERVICE_URL}/internal/stock/deduct",
                json={"tenant_id": tenant_id, "items": items},
                headers=SERVICE_HEADERS,
            )
            return resp.status_code == 200
    except Exception as e:
        logger.error(f"Stock deduction failed: {e}")
        return False


async def _restore_stock(tenant_id: str, items: List[Dict]):
    """Restore stock on invoice cancellation."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"{INVENTORY_SERVICE_URL}/internal/stock/restore",
                json={"tenant_id": tenant_id, "items": items},
                headers=SERVICE_HEADERS,
            )
    except Exception as e:
        logger.error(f"Stock restore failed: {e}")


async def _send_invoice_sms(phone: str, invoice_number: str, total: float, currency: str):
    """Queue SMS notification."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"{NOTIFICATION_SERVICE_URL}/internal/sms",
                json={"to": phone,
                      "message": f"Invoice {invoice_number} created. Total: {currency} {total:.2f}. "
                                 f"Thank you for your purchase!"},
                headers=SERVICE_HEADERS,
            )
    except Exception as e:
        logger.warning(f"SMS notification failed (non-critical): {e}")


@router.post("/")
async def create_invoice(payload: Dict[str, Any], db: Session = Depends(get_db),
                          user: Dict = Depends(require_billing_role)):
    """
    Create invoice with automatic tax calculation and stock deduction.
    Payload: {customer_name, customer_phone, customer_email, customer_id,
              region, currency, notes, due_date,
              items: [{product_id, product_name, product_sku, quantity,
                       price_per_unit, gst_percentage, tax_exempt, discount_pct}]}
    """
    tenant_id = user["tenant_id"]
    items_data = payload.get("items", [])
    if not items_data:
        raise HTTPException(status_code=400, detail="Invoice must have at least one item")

    region = payload.get("region", "india_gst")
    currency = payload.get("currency", "INR")
    country_code = payload.get("country_code", "IN")
    inter_state = payload.get("inter_state", False)

    # Calculate taxes
    tax_result = tax_engine.calculate_invoice_tax(items_data, region,
                                                    inter_state=inter_state,
                                                    country_code=country_code)

    # Deduct stock from inventory-service
    stock_items = [{"product_id": i["product_id"], "quantity": i["quantity"]} for i in items_data]
    stock_ok = await _deduct_stock(tenant_id, stock_items)
    if not stock_ok:
        raise HTTPException(status_code=409, detail="Insufficient stock for one or more items")

    # Create invoice
    invoice_number = generate_invoice_number(db, tenant_id)
    due_date = None
    if payload.get("due_date"):
        try:
            due_date = datetime.fromisoformat(payload["due_date"])
        except Exception:
            pass

    invoice = Invoice(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        invoice_number=invoice_number,
        user_id=user["user_id"],
        customer_id=payload.get("customer_id"),
        customer_name=payload.get("customer_name", "Walk-in Customer"),
        customer_phone=payload.get("customer_phone"),
        customer_email=payload.get("customer_email"),
        currency=currency,
        region=region,
        subtotal=tax_result["subtotal"],
        gst_amount=tax_result["cgst"] + tax_result["sgst"] + tax_result["igst"],
        vat_amount=tax_result["vat"],
        tax=tax_result["tax_total"],
        total_amount=tax_result["total"],
        amount_due=tax_result["total"],
        notes=payload.get("notes"),
        due_date=due_date,
        invoice_type=payload.get("invoice_type", "SALES"),
    )
    db.add(invoice)
    db.flush()

    # Create invoice items
    for item_data in items_data:
        qty = item_data["quantity"]
        price = item_data["price_per_unit"]
        gst_pct = item_data.get("gst_percentage", 0) or 0
        taxable = price * qty * (1 - item_data.get("discount_pct", 0) / 100)
        item_tax = tax_engine.calculate(taxable, region,
                                         product_tax_rate=item_data.get("gst_percentage"),
                                         tax_exempt=item_data.get("tax_exempt", False),
                                         inter_state=inter_state, country_code=country_code)

        warranty_expiry = None
        warranty_months = item_data.get("warranty_months", 0)
        if warranty_months and warranty_months > 0:
            warranty_expiry = datetime.utcnow() + timedelta(days=warranty_months * 30)

        inv_item = InvoiceItem(
            id=uuid.uuid4(),
            invoice_id=invoice.id,
            product_id=item_data["product_id"],
            product_name=item_data.get("product_name", "Product"),
            product_sku=item_data.get("product_sku"),
            quantity=qty,
            price_per_unit=price,
            discount_pct=item_data.get("discount_pct", 0),
            line_total=taxable + item_tax.tax_amount,
            gst_percentage=gst_pct if region == "india_gst" else None,
            cgst_amount=item_tax.breakdown.get("cgst"),
            sgst_amount=item_tax.breakdown.get("sgst"),
            igst_amount=item_tax.breakdown.get("igst"),
            vat_amount=item_tax.breakdown.get("vat"),
            tax_label=item_tax.tax_label,
            warranty_expiry_date=warranty_expiry,
        )
        db.add(inv_item)

    db.commit()
    db.refresh(invoice)

    # Send SMS (fire-and-forget)
    if invoice.customer_phone:
        import asyncio
        asyncio.create_task(_send_invoice_sms(invoice.customer_phone, invoice_number,
                                               invoice.total_amount, currency))

    return {
        "id": str(invoice.id),
        "invoice_number": invoice.invoice_number,
        "total_amount": invoice.total_amount,
        "currency": invoice.currency,
        "payment_status": invoice.payment_status,
        "region": invoice.region,
        "tax_breakdown": {"gst": invoice.gst_amount, "vat": invoice.vat_amount},
        "created_at": invoice.created_at.isoformat(),
    }


@router.get("/")
def list_invoices(skip: int = 0, limit: int = 50, status: Optional[str] = None,
                   db: Session = Depends(get_db), user: Dict = Depends(require_any_role)):
    q = db.query(Invoice).filter(Invoice.tenant_id == user["tenant_id"])
    if status:
        q = q.filter(Invoice.payment_status == status.upper())
    invoices = q.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()
    return [{"id": str(i.id), "invoice_number": i.invoice_number, "customer_name": i.customer_name,
             "total_amount": i.total_amount, "currency": i.currency,
             "payment_status": i.payment_status, "created_at": i.created_at.isoformat()}
            for i in invoices]


@router.get("/{invoice_id}")
def get_invoice(invoice_id: str, db: Session = Depends(get_db),
                user: Dict = Depends(require_any_role)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id,
                                        Invoice.tenant_id == user["tenant_id"]).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    items = db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice_id).all()
    return {
        "id": str(invoice.id), "invoice_number": invoice.invoice_number,
        "customer_name": invoice.customer_name, "customer_phone": invoice.customer_phone,
        "currency": invoice.currency, "subtotal": invoice.subtotal,
        "tax": invoice.tax, "gst_amount": invoice.gst_amount, "vat_amount": invoice.vat_amount,
        "total_amount": invoice.total_amount, "payment_status": invoice.payment_status,
        "amount_paid": invoice.amount_paid, "amount_due": invoice.amount_due,
        "region": invoice.region, "notes": invoice.notes,
        "created_at": invoice.created_at.isoformat(),
        "items": [{
            "product_name": i.product_name, "product_sku": i.product_sku,
            "quantity": i.quantity, "price_per_unit": i.price_per_unit,
            "gst_percentage": i.gst_percentage, "cgst_amount": i.cgst_amount,
            "sgst_amount": i.sgst_amount, "vat_amount": i.vat_amount,
            "line_total": i.line_total, "tax_label": i.tax_label,
            "warranty_expiry_date": i.warranty_expiry_date.isoformat() if i.warranty_expiry_date else None,
        } for i in items],
    }


@router.get("/{invoice_id}/pdf")
def download_invoice_pdf(invoice_id: str, db: Session = Depends(get_db),
                          user: Dict = Depends(require_any_role)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id,
                                        Invoice.tenant_id == user["tenant_id"]).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    items = db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice_id).all()
    pdf_buffer = generate_invoice_pdf(invoice, items)
    return StreamingResponse(pdf_buffer, media_type="application/pdf",
                              headers={"Content-Disposition":
                                       f"attachment; filename=invoice_{invoice.invoice_number}.pdf"})


@router.patch("/{invoice_id}/status")
def update_invoice_status(invoice_id: str, payload: Dict[str, Any],
                           db: Session = Depends(get_db), user: Dict = Depends(require_billing_role)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id,
                                        Invoice.tenant_id == user["tenant_id"]).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    new_status = payload.get("status", "").upper()
    if new_status not in ("PAID", "UNPAID", "PARTIAL", "OVERDUE", "CANCELLED"):
        raise HTTPException(status_code=400, detail="Invalid status")
    invoice.payment_status = new_status
    if new_status == "PAID":
        invoice.amount_paid = invoice.total_amount
        invoice.amount_due = 0
    amount_paid = payload.get("amount_paid")
    if amount_paid is not None:
        invoice.amount_paid = float(amount_paid)
        invoice.amount_due = max(0, invoice.total_amount - invoice.amount_paid)
    db.commit()
    return {"id": str(invoice.id), "payment_status": invoice.payment_status,
            "amount_paid": invoice.amount_paid, "amount_due": invoice.amount_due}


@router.get("/warranty/{phone}")
def warranty_lookup(phone: str, db: Session = Depends(get_db),
                    user: Dict = Depends(require_any_role)):
    from sqlalchemy import and_
    results = (db.query(InvoiceItem, Invoice)
               .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
               .filter(Invoice.tenant_id == user["tenant_id"],
                       Invoice.customer_phone == phone,
                       InvoiceItem.warranty_expiry_date.isnot(None))
               .all())
    return [{
        "product_name": item.product_name,
        "invoice_number": invoice.invoice_number,
        "customer_name": invoice.customer_name,
        "warranty_expiry": item.warranty_expiry_date.isoformat() if item.warranty_expiry_date else None,
        "warranty_active": item.warranty_expiry_date > datetime.utcnow() if item.warranty_expiry_date else False,
    } for item, invoice in results]
