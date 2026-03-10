import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, func, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    name = Column(String, nullable=False)
    contact_person = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    address = Column(String, nullable=True)

    # Procurement fields
    lead_time_days = Column(Integer, default=7)
    minimum_order_quantity = Column(Integer, default=1)
    preferred = Column(Boolean, default=False)
    api_endpoint = Column(String, nullable=True)  # Webhook for auto-ordering
    currency = Column(String(3), default="INR")

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User")
