import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    owner_user_id = Column(UUID(as_uuid=True), nullable=True)  # Set after user creation

    # Region & Locale
    country_code = Column(String(3), nullable=False, default="IN")  # ISO 3166-1
    currency = Column(String(3), nullable=False, default="INR")  # ISO 4217
    tax_region = Column(String(20), nullable=False, default="india_gst")  # india_gst, gcc_vat, eu_vat
    timezone = Column(String(50), nullable=False, default="Asia/Kolkata")

    # Storefront
    subdomain = Column(String(63), unique=True, nullable=False, index=True)

    # Subscription
    subscription_plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=True)
    subscription_expiry = Column(DateTime, nullable=True)

    # Business info
    gst_number = Column(String, nullable=True)
    pan_number = Column(String, nullable=True)
    business_address = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)

    # Invoice settings
    invoice_prefix = Column(String, default="SP")
    invoice_counter = Column(Integer, default=1)

    is_active = Column(Boolean, default=True)

    # Feature flags for agent safety
    allow_autonomous_agents = Column(Boolean, default=False)
    allow_dynamic_pricing = Column(Boolean, default=False)
    allow_auto_procurement = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subscription = relationship("SubscriptionPlan")
