"""
Notification logs and history — view sent notifications.
"""
import logging
from typing import Dict, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.notification_log import NotificationLog, SmsLog

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/logs")
def get_notification_logs(channel: Optional[str] = None, status: Optional[str] = None,
                           skip: int = 0, limit: int = 50,
                           db: Session = Depends(get_db), user: Dict = Depends(get_current_user)):
    q = db.query(NotificationLog).filter(NotificationLog.tenant_id == user["tenant_id"])
    if channel:
        q = q.filter(NotificationLog.channel == channel)
    if status:
        q = q.filter(NotificationLog.status == status)
    logs = q.order_by(NotificationLog.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": str(n.id), "channel": n.channel, "recipient": n.recipient,
            "subject": n.subject, "status": n.status, "provider": n.provider,
            "error_message": n.error_message, "sent_at": n.sent_at.isoformat() if n.sent_at else None,
            "created_at": n.created_at.isoformat(),
        }
        for n in logs
    ]


@router.get("/sms/logs")
def get_sms_logs(skip: int = 0, limit: int = 50,
                  db: Session = Depends(get_db), user: Dict = Depends(require_admin)):
    logs = db.query(SmsLog).filter(
        SmsLog.tenant_id == user["tenant_id"]
    ).order_by(SmsLog.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": str(s.id), "to_phone": s.to_phone, "status": s.status,
            "twilio_sid": s.twilio_sid, "price": s.price, "currency": s.currency,
            "error_code": s.error_code, "sent_at": s.sent_at.isoformat() if s.sent_at else None,
            "created_at": s.created_at.isoformat(),
        }
        for s in logs
    ]


@router.get("/stats")
def notification_stats(db: Session = Depends(get_db), user: Dict = Depends(require_admin)):
    from sqlalchemy import func
    stats = db.query(
        NotificationLog.channel,
        NotificationLog.status,
        func.count(NotificationLog.id).label("count")
    ).filter(NotificationLog.tenant_id == user["tenant_id"]).group_by(
        NotificationLog.channel, NotificationLog.status
    ).all()
    return [{"channel": s.channel, "status": s.status, "count": s.count} for s in stats]
