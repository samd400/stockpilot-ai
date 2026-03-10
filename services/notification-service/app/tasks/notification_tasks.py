"""
Celery tasks for async notification delivery and retries.
"""
import os
import logging
from celery import Celery

logger = logging.getLogger(__name__)

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
celery_app = Celery("notification-service", broker=CELERY_BROKER_URL, backend=CELERY_BROKER_URL)

celery_app.conf.beat_schedule = {
    "retry-failed-webhooks-every-5min": {
        "task": "app.tasks.notification_tasks.retry_failed_webhooks",
        "schedule": 300,  # 5 minutes
    },
    "cleanup-old-logs-daily": {
        "task": "app.tasks.notification_tasks.cleanup_old_logs",
        "schedule": 86400,  # 24 hours
    },
}


@celery_app.task(name="app.tasks.notification_tasks.send_sms_task")
def send_sms_task(tenant_id: str, to_phone: str, message: str):
    """Async SMS send task."""
    from app.services.sms_service import send_sms
    result = send_sms(to_phone, message, tenant_id)
    logger.info(f"SMS task: {to_phone} → {result.get('status')}")
    return result


@celery_app.task(name="app.tasks.notification_tasks.send_email_task")
def send_email_task(to_email: str, subject: str, html_content: str, to_name: str = None):
    """Async email send task."""
    from app.services.email_service import send_email
    result = send_email(to_email, subject, html_content, to_name)
    logger.info(f"Email task: {to_email} → {result.get('status')}")
    return result


@celery_app.task(name="app.tasks.notification_tasks.retry_failed_webhooks")
def retry_failed_webhooks():
    """Retry failed webhook deliveries with exponential backoff."""
    from app.core.database import SessionLocal
    from app.models.webhook_log import WebhookDelivery, WebhookEndpoint
    from app.services.webhook_service import deliver_webhook
    from datetime import datetime, timedelta

    db = SessionLocal()
    try:
        failed = db.query(WebhookDelivery).filter(
            WebhookDelivery.status == "failed",
            WebhookDelivery.retry_count < 5,
            WebhookDelivery.next_retry_at <= datetime.utcnow(),
        ).limit(50).all()

        for delivery in failed:
            endpoint = db.query(WebhookEndpoint).filter(WebhookEndpoint.id == delivery.endpoint_id).first()
            if not endpoint or not endpoint.is_active:
                continue

            result = deliver_webhook(endpoint.url, delivery.event, delivery.payload, endpoint.secret)
            delivery.retry_count += 1
            delivery.response_status = result.get("http_status")
            delivery.response_body = result.get("response_body", "")[:500]
            delivery.duration_ms = result.get("duration_ms")

            if result["status"] == "success":
                delivery.status = "success"
                delivery.delivered_at = datetime.utcnow()
            else:
                # Exponential backoff: 5min, 15min, 1h, 4h, 24h
                delays = [5, 15, 60, 240, 1440]
                delay = delays[min(delivery.retry_count, len(delays) - 1)]
                delivery.next_retry_at = datetime.utcnow() + timedelta(minutes=delay)

        db.commit()
        logger.info(f"Webhook retry task: processed {len(failed)} failed deliveries")
        return {"processed": len(failed)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.notification_tasks.cleanup_old_logs")
def cleanup_old_logs():
    """Delete notification logs older than 90 days."""
    from app.core.database import SessionLocal
    from app.models.notification_log import NotificationLog, SmsLog
    from datetime import datetime, timedelta
    from sqlalchemy import text

    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=90)
        n = db.execute(text("DELETE FROM notification_logs WHERE created_at < :cutoff"), {"cutoff": cutoff})
        s = db.execute(text("DELETE FROM sms_logs WHERE created_at < :cutoff"), {"cutoff": cutoff})
        db.commit()
        logger.info("Cleanup: deleted old notification logs")
        return {"message": "Cleanup done"}
    finally:
        db.close()
