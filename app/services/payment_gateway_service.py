import os
import stripe
import razorpay
import requests
import hashlib
import hmac
from app.models.payment_transaction import PaymentTransaction
from app.models.user_subscription import UserSubscription
from app.models.invoice import Invoice
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

# Initialize payment gateways
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_your_key")
razorpay_client = razorpay.Client(
    auth=(
        os.getenv("RAZORPAY_KEY_ID", "your_key_id"),
        os.getenv("RAZORPAY_KEY_SECRET", "your_key_secret")
    )
)

# Paytabs config
PAYTABS_SERVER_KEY = os.getenv("PAYTABS_SERVER_KEY", "")
PAYTABS_PROFILE_ID = os.getenv("PAYTABS_PROFILE_ID", "")
PAYTABS_BASE_URL = os.getenv("PAYTABS_BASE_URL", "https://secure.paytabs.sa")


class StripePaymentService:
    """Stripe payment integration — Europe/Global"""

    @staticmethod
    def create_payment_intent(amount: float, currency: str = "usd", metadata: dict = None):
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency=currency.lower(),
                metadata=metadata or {}
            )
            return {
                "status": "success",
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def create_subscription(customer_id: str, price_id: str):
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                payment_behavior="default_incomplete",
                expand=["latest_invoice.payment_intent"]
            )
            return {
                "status": "success",
                "subscription_id": subscription.id,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe subscription error: {str(e)}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def retrieve_payment_intent(payment_intent_id: str):
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                "status": intent.status,
                "amount": intent.amount / 100,
                "currency": intent.currency
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe retrieval error: {str(e)}")
            return None


class RazorpayPaymentService:
    """Razorpay payment integration — India"""

    @staticmethod
    def create_order(amount: float, currency: str = "INR", receipt: str = None):
        try:
            order = razorpay_client.order.create(
                amount=int(amount * 100),
                currency=currency.upper(),
                receipt=receipt or "receipt",
                payment_capture=1
            )
            return {
                "status": "success",
                "order_id": order["id"],
                "amount": order["amount"] / 100
            }
        except Exception as e:
            logger.error(f"Razorpay error: {str(e)}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def verify_payment(payment_id: str, order_id: str, signature: str):
        try:
            razorpay_client.utility.verify_payment_signature({
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature
            })
            return {"status": "verified"}
        except razorpay.errors.SignatureVerificationError:
            logger.error("Razorpay signature verification failed")
            return {"status": "failed"}

    @staticmethod
    def create_subscription(plan_id: str, customer_notify: int = 1):
        try:
            subscription = razorpay_client.subscription.create(
                plan_id=plan_id,
                customer_notify=customer_notify,
                quantity=1,
                total_count=12
            )
            return {
                "status": "success",
                "subscription_id": subscription["id"]
            }
        except Exception as e:
            logger.error(f"Razorpay subscription error: {str(e)}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def retrieve_payment(payment_id: str):
        try:
            payment = razorpay_client.payment.fetch(payment_id)
            return {
                "status": payment["status"],
                "amount": payment["amount"] / 100,
                "currency": payment["currency"]
            }
        except Exception as e:
            logger.error(f"Razorpay retrieval error: {str(e)}")
            return None


class PaytabsPaymentService:
    """Paytabs payment integration — GCC region."""

    @staticmethod
    def create_payment_page(amount: float, currency: str = "SAR",
                             cart_id: str = "", cart_description: str = "",
                             customer_name: str = "", customer_email: str = "",
                             customer_phone: str = "", callback_url: str = "",
                             return_url: str = ""):
        """Create a Paytabs hosted payment page."""
        try:
            headers = {
                "authorization": PAYTABS_SERVER_KEY,
                "content-type": "application/json"
            }
            payload = {
                "profile_id": PAYTABS_PROFILE_ID,
                "tran_type": "sale",
                "tran_class": "ecom",
                "cart_id": cart_id,
                "cart_description": cart_description,
                "cart_currency": currency.upper(),
                "cart_amount": amount,
                "callback": callback_url,
                "return": return_url,
                "customer_details": {
                    "name": customer_name,
                    "email": customer_email,
                    "phone": customer_phone,
                }
            }

            response = requests.post(
                f"{PAYTABS_BASE_URL}/payment/request",
                json=payload,
                headers=headers,
                timeout=30
            )
            data = response.json()

            if "redirect_url" in data:
                return {
                    "status": "success",
                    "redirect_url": data["redirect_url"],
                    "tran_ref": data.get("tran_ref")
                }
            else:
                return {
                    "status": "error",
                    "message": data.get("message", "Payment creation failed")
                }
        except Exception as e:
            logger.error(f"Paytabs error: {str(e)}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def verify_payment(tran_ref: str):
        """Query Paytabs transaction status."""
        try:
            headers = {
                "authorization": PAYTABS_SERVER_KEY,
                "content-type": "application/json"
            }
            payload = {
                "profile_id": PAYTABS_PROFILE_ID,
                "tran_ref": tran_ref
            }
            response = requests.post(
                f"{PAYTABS_BASE_URL}/payment/query",
                json=payload,
                headers=headers,
                timeout=30
            )
            data = response.json()
            return {
                "status": data.get("payment_result", {}).get("response_status", "error"),
                "tran_ref": data.get("tran_ref"),
                "amount": data.get("cart_amount"),
                "currency": data.get("cart_currency"),
            }
        except Exception as e:
            logger.error(f"Paytabs verify error: {str(e)}")
            return None


# ===== Region-based gateway selector =====

def get_payment_service(region: str):
    """Select payment gateway based on tenant's tax region."""
    region_map = {
        "india_gst": "razorpay",
        "gcc_vat": "paytabs",
        "eu_vat": "stripe",
    }
    gateway = region_map.get(region, "stripe")

    services = {
        "stripe": StripePaymentService,
        "razorpay": RazorpayPaymentService,
        "paytabs": PaytabsPaymentService,
    }
    return services[gateway], gateway


def save_payment_transaction(
    db: Session,
    user_id,
    amount: float,
    gateway: str,
    gateway_transaction_id: str,
    status: str,
    tenant_id=None,
    invoice_id=None,
    subscription_id=None,
    description: str = None,
    currency: str = "USD"
):
    """Save payment transaction to database."""
    transaction = PaymentTransaction(
        tenant_id=tenant_id,
        user_id=user_id,
        amount=amount,
        currency=currency,
        gateway=gateway,
        gateway_transaction_id=gateway_transaction_id,
        status=status,
        invoice_id=invoice_id,
        subscription_id=subscription_id,
        description=description
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction
