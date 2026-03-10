"""
Email delivery via SendGrid. Supports HTML templates.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
FROM_EMAIL = os.getenv("EMAIL_FROM", "noreply@stockpilot.app")
FROM_NAME = os.getenv("EMAIL_FROM_NAME", "StockPilot")


def send_email(to_email: str, subject: str, html_content: str,
               to_name: Optional[str] = None) -> dict:
    """Send email via SendGrid. Falls back to log if not configured."""
    if not SENDGRID_API_KEY:
        logger.warning(f"[EMAIL DRY RUN] To: {to_email} | Subject: {subject}")
        return {"status": "dry_run", "to": to_email}

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, To, From

        message = Mail(
            from_email=From(FROM_EMAIL, FROM_NAME),
            to_emails=To(to_email, to_name or to_email),
            subject=subject,
            html_content=html_content,
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(f"Email sent to {to_email}: status={response.status_code}")
        return {"status": "sent", "to": to_email, "http_status": response.status_code}
    except Exception as e:
        logger.error(f"Email failed to {to_email}: {e}")
        return {"status": "failed", "error": str(e), "to": to_email}


def send_invoice_email(to_email: str, customer_name: str, invoice_number: str,
                        amount: float, currency: str, pdf_url: Optional[str] = None) -> dict:
    """Invoice created notification email."""
    currency_symbols = {"INR": "₹", "AED": "AED", "SAR": "SAR", "EUR": "€", "GBP": "£", "USD": "$"}
    symbol = currency_symbols.get(currency, currency)

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2563eb;">Invoice Generated</h2>
        <p>Dear {customer_name},</p>
        <p>Your invoice <strong>#{invoice_number}</strong> for <strong>{symbol}{amount:.2f}</strong> has been generated.</p>
        {"<p><a href='" + pdf_url + "' style='background:#2563eb;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;'>Download Invoice PDF</a></p>" if pdf_url else ""}
        <p>Thank you for your business!</p>
        <hr>
        <p style="color:#666;font-size:12px;">StockPilot — Intelligent Inventory Management</p>
    </div>
    """
    return send_email(to_email, f"Invoice #{invoice_number} — {symbol}{amount:.2f}", html, customer_name)


def send_welcome_email(to_email: str, business_name: str, user_name: str) -> dict:
    """Welcome email after registration."""
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2563eb;">Welcome to StockPilot!</h2>
        <p>Hi {user_name},</p>
        <p>Your business <strong>{business_name}</strong> is now set up on StockPilot.</p>
        <p>You can now:</p>
        <ul>
            <li>Add products and manage inventory</li>
            <li>Create invoices and process payments</li>
            <li>Monitor business health with AI insights</li>
        </ul>
        <p>Log in at <a href="https://app.stockpilot.app">app.stockpilot.app</a></p>
        <hr>
        <p style="color:#666;font-size:12px;">StockPilot — Intelligent Inventory Management</p>
    </div>
    """
    return send_email(to_email, "Welcome to StockPilot!", html, user_name)


def send_low_stock_email(to_email: str, product_name: str, quantity: int,
                          reorder_level: int) -> dict:
    """Low stock alert email."""
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #dc2626;">⚠️ Low Stock Alert</h2>
        <p><strong>{product_name}</strong> is running low.</p>
        <table style="border-collapse:collapse; width:100%;">
            <tr><td style="padding:8px;border:1px solid #ddd;">Current Stock</td>
                <td style="padding:8px;border:1px solid #ddd;color:#dc2626;">{quantity} units</td></tr>
            <tr><td style="padding:8px;border:1px solid #ddd;">Reorder Level</td>
                <td style="padding:8px;border:1px solid #ddd;">{reorder_level} units</td></tr>
        </table>
        <p>Please create a purchase order to restock.</p>
        <hr>
        <p style="color:#666;font-size:12px;">StockPilot — Intelligent Inventory Management</p>
    </div>
    """
    return send_email(to_email, f"Low Stock Alert: {product_name}", html)
