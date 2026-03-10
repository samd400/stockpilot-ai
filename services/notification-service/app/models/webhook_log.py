import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class WebhookEndpoint(Base):
    """Tenant-configured webhook destinations."""
    __tablename__ = "webhook_endpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    url = Column(String, nullable=False)
    secret = Column(String, nullable=True)  # HMAC signing secret
    events = Column(JSONB, default=list)    # ["invoice.created", "stock.low", "payment.received"]
    is_active = Column(Boolean, default=True)
    description = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class WebhookDelivery(Base):
    """Log of webhook delivery attempts."""
    __tablename__ = "webhook_deliveries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    event = Column(String, nullable=False)
    payload = Column(JSONB, nullable=True)
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    duration_ms = Column(Float, nullable=True)

    status = Column(String, default="pending")  # pending, success, failed
    retry_count = Column(Integer, default=0)
    next_retry_at = Column(DateTime, nullable=True)

    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
