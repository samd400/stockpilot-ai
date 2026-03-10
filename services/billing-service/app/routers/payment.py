import uuid
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_billing_role
from app.models.payment import Payment, PaymentStatus, PaymentMode
from app.models.payment_transaction import PaymentTransaction
from app.models.invoice import Invoice
from app.services import payment_gateway_service as gw

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/")
def record_payment(payload: Dict[str, Any], db: Session = Depends(get_db),
                   user: Dict = Depends(require_billing_role)):
    invoice = db.query(Invoice).filter(Invoice.id == payload.get("invoice_id"),
                                        Invoice.tenant_id == user["tenant_id"]).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    payment = Payment(
        id=uuid.uuid4(), tenant_id=user["tenant_id"],
        invoice_id=invoice.id, user_id=user["user_id"],
        amount=payload["amount"], currency=payload.get("currency", "INR"),
        status=PaymentStatus.PAID,
        mode=PaymentMode(payload.get("mode", "CASH").upper()),
        transaction_id=payload.get("transaction_id"),
        notes=payload.get("notes"),
    )
    db.add(payment)
    invoice.amount_paid = (invoice.amount_paid or 0) + payload["amount"]
    invoice.amount_due = max(0, invoice.total_amount - invoice.amount_paid)
    if invoice.amount_due <= 0:
        invoice.payment_status = "PAID"
    elif invoice.amount_paid > 0:
        invoice.payment_status = "PARTIAL"
    db.commit()
    db.refresh(payment)
    return {"id": str(payment.id), "status": payment.status.value, "amount": payment.amount}


@router.get("/")
def list_payments(invoice_id: str = None, db: Session = Depends(get_db),
                  user: Dict = Depends(get_current_user)):
    q = db.query(Payment).filter(Payment.tenant_id == user["tenant_id"])
    if invoice_id:
        q = q.filter(Payment.invoice_id == invoice_id)
    payments = q.order_by(Payment.created_at.desc()).all()
    return [{"id": str(p.id), "invoice_id": str(p.invoice_id), "amount": p.amount,
             "currency": p.currency, "status": p.status.value, "mode": p.mode.value if p.mode else None,
             "created_at": p.created_at.isoformat()} for p in payments]


@router.post("/stripe/intent")
def create_stripe_intent(payload: Dict[str, Any], user: Dict = Depends(require_billing_role)):
    try:
        result = gw.create_stripe_payment_intent(
            amount=payload["amount"], currency=payload.get("currency", "usd"),
            metadata={"tenant_id": user["tenant_id"], "invoice_id": payload.get("invoice_id", "")},
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/razorpay/order")
def create_razorpay_order(payload: Dict[str, Any], user: Dict = Depends(require_billing_role)):
    try:
        result = gw.create_razorpay_order(
            amount=payload["amount"], currency=payload.get("currency", "INR"),
            receipt=payload.get("invoice_id", str(uuid.uuid4())),
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify")
def verify_payment(payload: Dict[str, Any], db: Session = Depends(get_db),
                   user: Dict = Depends(require_billing_role)):
    gateway = payload.get("gateway", "razorpay")
    if gateway == "razorpay":
        verified = gw.verify_razorpay_payment(
            payload["order_id"], payload["payment_id"], payload["signature"]
        )
        if not verified:
            raise HTTPException(status_code=400, detail="Payment verification failed")
        txn = PaymentTransaction(
            id=uuid.uuid4(), tenant_id=user["tenant_id"],
            gateway="razorpay",
            gateway_order_id=payload["order_id"],
            gateway_payment_id=payload["payment_id"],
            gateway_signature=payload["signature"],
            amount=payload.get("amount", 0),
            currency=payload.get("currency", "INR"),
            status="captured",
        )
        db.add(txn)
        db.commit()
        return {"verified": True, "transaction_id": str(txn.id)}
    raise HTTPException(status_code=400, detail=f"Unsupported gateway: {gateway}")


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = gw.verify_stripe_webhook(payload, sig)
        event_type = event.get("event_type")
        if event_type == "payment_intent.succeeded":
            logger.info(f"Stripe payment succeeded: {event.get('data', {}).get('id')}")
        return {"received": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
