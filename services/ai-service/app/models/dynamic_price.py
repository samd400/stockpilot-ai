import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class DynamicPrice(Base):
    __tablename__ = "dynamic_prices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), nullable=False)
    base_price = Column(Float, nullable=True)
    suggested_price = Column(Float, nullable=False)
    adjustment_reason = Column(String(500), nullable=True)
    confidence = Column(Float, default=0.8)
    valid_until = Column(DateTime, nullable=True)
    applied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
