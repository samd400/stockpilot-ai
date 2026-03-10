import uuid
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.deps import require_billing_role

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pos", tags=["POS"])


@router.post("/sale")
async def pos_sale(payload: Dict[str, Any], db: Session = Depends(get_db),
                   user: Dict = Depends(require_billing_role)):
    """Quick POS sale — creates invoice + records payment in one step."""
    from app.routers.invoice import create_invoice
    from app.models.invoice import Invoice
    from app.models.payment import Payment, PaymentStatus, PaymentMode

    # Create invoice
    invoice_data = {**payload, "invoice_type": "SALES"}
    invoice_response = await create_invoice(invoice_data, db, user)
    invoice_id = invoice_response["id"]

    # Auto-record payment if payment_mode provided
    payment_mode = payload.get("payment_mode", "CASH").upper()
    if payment_mode:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if invoice:
            payment = Payment(
                id=uuid.uuid4(), tenant_id=user["tenant_id"],
                invoice_id=invoice.id, user_id=user["user_id"],
                amount=invoice.total_amount, currency=invoice.currency,
                status=PaymentStatus.PAID, mode=PaymentMode(payment_mode),
            )
            db.add(payment)
            invoice.payment_status = "PAID"
            invoice.amount_paid = invoice.total_amount
            invoice.amount_due = 0
            db.commit()

    return {**invoice_response, "payment_mode": payment_mode, "payment_status": "PAID"}


@router.get("/session")
def pos_session(db: Session = Depends(get_db), user: Dict = Depends(require_billing_role)):
    """Today's POS session stats."""
    from app.models.invoice import Invoice
    from datetime import date
    today = date.today()
    invoices = db.query(Invoice).filter(
        Invoice.tenant_id == user["tenant_id"],
        func.date(Invoice.created_at) == today,
        Invoice.invoice_type == "SALES",
    ).all()
    total_sales = sum(i.total_amount for i in invoices)
    total_invoices = len(invoices)
    paid_invoices = sum(1 for i in invoices if i.payment_status == "PAID")
    return {
        "date": str(today),
        "total_invoices": total_invoices,
        "paid_invoices": paid_invoices,
        "total_sales": round(total_sales, 2),
        "currency": invoices[0].currency if invoices else "INR",
    }
