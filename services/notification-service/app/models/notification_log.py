import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class NotificationLog(Base):
    """Tracks all notifications sent across all channels."""
    __tablename__ = "notification_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    channel = Column(String, nullable=False)  # sms, email, push, webhook
    recipient = Column(String, nullable=False)  # phone/email/device_token
    template_name = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    message = Column(Text, nullable=False)

    status = Column(String, default="pending")  # pending, sent, failed, bounced
    provider = Column(String, nullable=True)    # twilio, sendgrid, firebase
    provider_message_id = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SmsLog(Base):
    """Detailed SMS log with Twilio metadata."""
    __tablename__ = "sms_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    notification_id = Column(UUID(as_uuid=True), nullable=True)

    to_phone = Column(String, nullable=False)
    from_phone = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    status = Column(String, default="queued")  # queued, sent, delivered, failed
    twilio_sid = Column(String, nullable=True)
    price = Column(String, nullable=True)
    currency = Column(String(3), nullable=True)
    error_code = Column(String, nullable=True)

    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
