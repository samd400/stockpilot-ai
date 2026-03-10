import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    owner_user_id = Column(UUID(as_uuid=True), nullable=True)

    # Region & Locale
    country_code = Column(String(3), default="IN", nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    tax_region = Column(String(20), default="india_gst", nullable=False)
    timezone = Column(String(50), default="Asia/Kolkata", nullable=False)

    subdomain = Column(String(63), unique=True, nullable=False, index=True)
    subscription_plan_id = Column(UUID(as_uuid=True), nullable=True)
    subscription_expiry = Column(DateTime, nullable=True)

    gst_number = Column(String(20), nullable=True)
    pan_number = Column(String(20), nullable=True)
    business_address = Column(String(500), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    logo_url = Column(String(500), nullable=True)

    invoice_prefix = Column(String(10), default="SP", nullable=False)
    invoice_counter = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Feature flags
    allow_autonomous_agents = Column(Boolean, default=False)
    allow_dynamic_pricing = Column(Boolean, default=False)
    allow_auto_procurement = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = relationship("User", back_populates="tenant", foreign_keys="User.tenant_id")
