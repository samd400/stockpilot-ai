"""
SMS delivery via Twilio. Supports India, GCC, Europe.
"""
import os
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")


def send_sms(to_phone: str, message: str, tenant_id: str = None) -> dict:
    """
    Send SMS via Twilio. Returns status dict.
    Falls back to logging if Twilio not configured.
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        logger.warning(f"[SMS DRY RUN] To: {to_phone} | Message: {message}")
        return {"status": "dry_run", "to": to_phone, "message": message}

    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=message,
            from_=TWILIO_FROM_NUMBER,
            to=to_phone
        )
        logger.info(f"SMS sent to {to_phone}: SID={msg.sid}")
        return {
            "status": "sent",
            "sid": msg.sid,
            "to": to_phone,
            "price": str(msg.price) if msg.price else None,
            "currency": msg.price_unit,
        }
    except Exception as e:
        logger.error(f"SMS failed to {to_phone}: {e}")
        return {"status": "failed", "error": str(e), "to": to_phone}


def send_invoice_sms(to_phone: str, customer_name: str, invoice_number: str,
                     amount: float, currency: str) -> dict:
    """Pre-built template: invoice notification."""
    currency_symbols = {"INR": "₹", "AED": "AED", "SAR": "SAR", "EUR": "€", "GBP": "£", "USD": "$"}
    symbol = currency_symbols.get(currency, currency)
    message = (
        f"Hi {customer_name}, your invoice #{invoice_number} "
        f"for {symbol}{amount:.2f} has been generated. "
        f"Thank you for your business! — StockPilot"
    )
    return send_sms(to_phone, message)


def send_payment_sms(to_phone: str, customer_name: str, amount: float, currency: str) -> dict:
    """Pre-built template: payment received notification."""
    currency_symbols = {"INR": "₹", "AED": "AED", "SAR": "SAR", "EUR": "€", "GBP": "£", "USD": "$"}
    symbol = currency_symbols.get(currency, currency)
    message = (
        f"Hi {customer_name}, we've received your payment of "
        f"{symbol}{amount:.2f}. Thank you! — StockPilot"
    )
    return send_sms(to_phone, message)


def send_low_stock_sms(to_phone: str, product_name: str, quantity: int) -> dict:
    """Pre-built template: low stock alert."""
    message = (
        f"⚠️ Low Stock Alert: {product_name} has only {quantity} units remaining. "
        f"Please reorder soon. — StockPilot"
    )
    return send_sms(to_phone, message)
