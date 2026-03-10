"""
Payment Gateway Abstraction — Stripe, Razorpay, PayTabs.
"""
import os
import hmac
import hashlib
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
PAYTABS_SERVER_KEY = os.getenv("PAYTABS_SERVER_KEY", "")
PAYTABS_PROFILE_ID = os.getenv("PAYTABS_PROFILE_ID", "")
PAYTABS_REGION = os.getenv("PAYTABS_REGION", "ARE")


# ─── Stripe ──────────────────────────────────────────────────────────────────

def create_stripe_payment_intent(amount: float, currency: str,
                                  metadata: Dict[str, str] = None) -> Dict[str, Any]:
    if not STRIPE_SECRET_KEY:
        raise ValueError("STRIPE_SECRET_KEY not configured")
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Stripe uses smallest currency unit
            currency=currency.lower(),
            metadata=metadata or {},
            payment_method_types=["card"],
        )
        return {"client_secret": intent.client_secret, "payment_intent_id": intent.id,
                "amount": amount, "currency": currency}
    except Exception as e:
        logger.error(f"Stripe payment intent failed: {e}")
        raise


def verify_stripe_webhook(payload: bytes, signature: str, secret: str = None) -> Dict[str, Any]:
    if not STRIPE_WEBHOOK_SECRET and not secret:
        raise ValueError("STRIPE_WEBHOOK_SECRET not configured")
    try:
        import stripe
        event = stripe.Webhook.construct_event(
            payload, signature, secret or STRIPE_WEBHOOK_SECRET
        )
        return {"event_type": event["type"], "data": event["data"]["object"]}
    except Exception as e:
        logger.error(f"Stripe webhook verification failed: {e}")
        raise


# ─── Razorpay ────────────────────────────────────────────────────────────────

def create_razorpay_order(amount: float, currency: str, receipt: str) -> Dict[str, Any]:
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise ValueError("Razorpay credentials not configured")
    try:
        import razorpay
        client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        order = client.order.create({
            "amount": int(amount * 100),  # paise
            "currency": currency.upper(),
            "receipt": receipt,
            "payment_capture": 1,
        })
        return {"order_id": order["id"], "amount": amount, "currency": currency,
                "key_id": RAZORPAY_KEY_ID}
    except Exception as e:
        logger.error(f"Razorpay order creation failed: {e}")
        raise


def verify_razorpay_payment(order_id: str, payment_id: str, signature: str) -> bool:
    if not RAZORPAY_KEY_SECRET:
        raise ValueError("RAZORPAY_KEY_SECRET not configured")
    try:
        message = f"{order_id}|{payment_id}"
        expected = hmac.new(RAZORPAY_KEY_SECRET.encode(), message.encode(),
                             hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception as e:
        logger.error(f"Razorpay verification failed: {e}")
        return False


# ─── PayTabs ──────────────────────────────────────────────────────────────────

def create_paytabs_payment(amount: float, currency: str, customer: Dict[str, str],
                            return_url: str, callback_url: str = "") -> Dict[str, Any]:
    if not PAYTABS_SERVER_KEY or not PAYTABS_PROFILE_ID:
        raise ValueError("PayTabs credentials not configured")
    import requests
    url = f"https://secure.paytabs.com/payment/request"
    payload = {
        "profile_id": PAYTABS_PROFILE_ID,
        "tran_type": "sale",
        "tran_class": "ecom",
        "cart_id": f"order-{customer.get('reference', 'unknown')}",
        "cart_description": customer.get("description", "StockPilot Order"),
        "cart_currency": currency.upper(),
        "cart_amount": amount,
        "callback": callback_url or return_url,
        "return": return_url,
        "customer_details": {
            "name": customer.get("name", "Customer"),
            "email": customer.get("email", ""),
            "phone": customer.get("phone", ""),
            "street1": customer.get("address", ""),
            "city": customer.get("city", ""),
            "country": customer.get("country", "AE"),
        },
    }
    headers = {"authorization": PAYTABS_SERVER_KEY, "content-type": "application/json"}
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return {"payment_url": data.get("redirect_url"), "tran_ref": data.get("tran_ref"),
            "result": data}
