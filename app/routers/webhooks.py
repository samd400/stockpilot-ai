"""
Payment Webhook Handlers — for Stripe, Razorpay, Paytabs callbacks.
"""

from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.core.database import SessionLocal
from app.models.payment_transaction import PaymentTransaction
from app.models.invoice import Invoice
import stripe
import os
import logging
import json
import hmac
import hashlib

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")


@router.post("/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        if STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        else:
            event = json.loads(payload)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid webhook")

    db = SessionLocal()
    try:
        event_type = event.get("type", "")

        if event_type == "payment_intent.succeeded":
            pi = event["data"]["object"]
            txn = db.query(PaymentTransaction).filter(
                PaymentTransaction.gateway_transaction_id == pi["id"]
            ).first()
            if txn:
                txn.status = "SUCCESS"
                if txn.invoice_id:
                    invoice = db.query(Invoice).filter(Invoice.id == txn.invoice_id).first()
                    if invoice:
                        invoice.amount_paid += txn.amount
                        if invoice.amount_paid >= invoice.total_amount:
                            invoice.payment_status = "PAID"
                            invoice.amount_due = 0
                        else:
                            invoice.payment_status = "PARTIAL"
                            invoice.amount_due = invoice.total_amount - invoice.amount_paid
                db.commit()

        elif event_type == "payment_intent.payment_failed":
            pi = event["data"]["object"]
            txn = db.query(PaymentTransaction).filter(
                PaymentTransaction.gateway_transaction_id == pi["id"]
            ).first()
            if txn:
                txn.status = "FAILED"
                db.commit()

    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
    finally:
        db.close()

    return {"status": "ok"}


@router.post("/razorpay")
async def razorpay_webhook(request: Request):
    """Handle Razorpay webhook events."""
    payload = await request.body()
    payload_json = json.loads(payload)

    db = SessionLocal()
    try:
        event_type = payload_json.get("event", "")
        payment_entity = payload_json.get("payload", {}).get("payment", {}).get("entity", {})

        if event_type == "payment.captured":
            order_id = payment_entity.get("order_id")
            txn = db.query(PaymentTransaction).filter(
                PaymentTransaction.gateway_transaction_id == order_id
            ).first()
            if txn:
                txn.status = "SUCCESS"
                if txn.invoice_id:
                    invoice = db.query(Invoice).filter(Invoice.id == txn.invoice_id).first()
                    if invoice:
                        invoice.amount_paid += txn.amount
                        if invoice.amount_paid >= invoice.total_amount:
                            invoice.payment_status = "PAID"
                            invoice.amount_due = 0
                db.commit()

        elif event_type == "payment.failed":
            order_id = payment_entity.get("order_id")
            txn = db.query(PaymentTransaction).filter(
                PaymentTransaction.gateway_transaction_id == order_id
            ).first()
            if txn:
                txn.status = "FAILED"
                db.commit()

    except Exception as e:
        logger.error(f"Razorpay webhook error: {e}")
    finally:
        db.close()

    return {"status": "ok"}


@router.post("/paytabs")
async def paytabs_webhook(request: Request):
    """Handle Paytabs callback."""
    payload = await request.body()
    payload_json = json.loads(payload)

    db = SessionLocal()
    try:
        tran_ref = payload_json.get("tran_ref")
        response_status = payload_json.get("payment_result", {}).get("response_status", "")

        if tran_ref:
            txn = db.query(PaymentTransaction).filter(
                PaymentTransaction.gateway_transaction_id == tran_ref
            ).first()
            if txn:
                if response_status == "A":  # Authorized
                    txn.status = "SUCCESS"
                    if txn.invoice_id:
                        invoice = db.query(Invoice).filter(Invoice.id == txn.invoice_id).first()
                        if invoice:
                            invoice.amount_paid += txn.amount
                            if invoice.amount_paid >= invoice.total_amount:
                                invoice.payment_status = "PAID"
                                invoice.amount_due = 0
                else:
                    txn.status = "FAILED"
                db.commit()

    except Exception as e:
        logger.error(f"Paytabs webhook error: {e}")
    finally:
        db.close()

    return {"status": "ok"}
