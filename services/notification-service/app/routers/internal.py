"""
Internal endpoints — called by other microservices to send notifications.
Protected by X-Service-Token header.
"""
import uuid
import logging
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import verify_service_token
from app.models.notification_log import NotificationLog, SmsLog
from app.models.webhook_log import WebhookEndpoint
from app.services import sms_service, email_service, webhook_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/internal", tags=["Internal"])


def _log_notification(db: Session, tenant_id: str, channel: str, recipient: str,
                       message: str, subject: str, status: str, provider: str,
                       provider_message_id: str = None, error: str = None):
    log = NotificationLog(
        id=uuid.uuid4(), tenant_id=tenant_id, channel=channel, recipient=recipient,
        message=message, subject=subject, status=status, provider=provider,
        provider_message_id=provider_message_id, error_message=error,
        sent_at=datetime.utcnow() if status == "sent" else None,
    )
    db.add(log)
    db.commit()


@router.post("/notify/sms")
async def send_sms_internal(payload: Dict[str, Any], background_tasks: BackgroundTasks,
                             db: Session = Depends(get_db), _: bool = Depends(verify_service_token)):
    """Send SMS notification. Called by billing, inventory services."""
    tenant_id = payload["tenant_id"]
    to_phone = payload["to_phone"]
    message = payload["message"]
    template = payload.get("template")

    def _send():
        if template == "invoice":
            result = sms_service.send_invoice_sms(
                to_phone, payload.get("customer_name", ""),
                payload.get("invoice_number", ""), payload.get("amount", 0),
                payload.get("currency", "INR")
            )
        elif template == "payment":
            result = sms_service.send_payment_sms(
                to_phone, payload.get("customer_name", ""),
                payload.get("amount", 0), payload.get("currency", "INR")
            )
        elif template == "low_stock":
            result = sms_service.send_low_stock_sms(
                to_phone, payload.get("product_name", ""), payload.get("quantity", 0)
            )
        else:
            result = sms_service.send_sms(to_phone, message, tenant_id)

        with db as session:
            _log_notification(
                session, tenant_id, "sms", to_phone, message, None,
                result.get("status", "failed"), "twilio",
                result.get("sid"), result.get("error")
            )

    background_tasks.add_task(_send)
    return {"message": "SMS queued"}


@router.post("/notify/email")
async def send_email_internal(payload: Dict[str, Any], background_tasks: BackgroundTasks,
                               db: Session = Depends(get_db), _: bool = Depends(verify_service_token)):
    """Send email notification. Called by billing and auth services."""
    tenant_id = payload["tenant_id"]
    to_email = payload["to_email"]
    template = payload.get("template")

    def _send():
        if template == "invoice":
            result = email_service.send_invoice_email(
                to_email, payload.get("customer_name", ""),
                payload.get("invoice_number", ""), payload.get("amount", 0),
                payload.get("currency", "INR"), payload.get("pdf_url")
            )
        elif template == "welcome":
            result = email_service.send_welcome_email(
                to_email, payload.get("business_name", ""), payload.get("user_name", "")
            )
        elif template == "low_stock":
            result = email_service.send_low_stock_email(
                to_email, payload.get("product_name", ""),
                payload.get("quantity", 0), payload.get("reorder_level", 10)
            )
        else:
            result = email_service.send_email(
                to_email, payload.get("subject", "Notification"),
                payload.get("html_content", payload.get("message", ""))
            )

        with db as session:
            _log_notification(
                session, tenant_id, "email", to_email,
                payload.get("message", "")[:500], payload.get("subject"),
                result.get("status", "failed"), "sendgrid",
                None, result.get("error")
            )

    background_tasks.add_task(_send)
    return {"message": "Email queued"}


@router.post("/notify/webhook")
async def send_webhook_internal(payload: Dict[str, Any], background_tasks: BackgroundTasks,
                                 db: Session = Depends(get_db), _: bool = Depends(verify_service_token)):
    """Broadcast webhook event to all registered endpoints for a tenant."""
    tenant_id = payload["tenant_id"]
    event = payload["event"]
    data = payload.get("data", {})

    endpoints = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.tenant_id == tenant_id,
        WebhookEndpoint.is_active == True
    ).all()

    def _deliver():
        results = webhook_service.deliver_to_all_endpoints(endpoints, event, data)
        logger.info(f"Webhook {event} for tenant {tenant_id}: {len(results)} endpoints notified")

    if endpoints:
        background_tasks.add_task(_deliver)

    return {"message": f"Webhook {event} queued for {len(endpoints)} endpoints"}
