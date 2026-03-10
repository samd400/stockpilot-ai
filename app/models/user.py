import uuid
import enum
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.core.database import Base
from sqlalchemy.orm import relationship


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    STAFF = "staff"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Auth
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.ADMIN)

    # Profile (kept for backward compat)
    business_name = Column(String, nullable=True)
    owner_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    # Legacy fields (kept for backward compat, prefer tenant-level)
    subscription_plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=True)
    gst_number = Column(String, nullable=True)
    pan_number = Column(String, nullable=True)
    business_address = Column(String, nullable=True)
    subscription_expiry = Column(DateTime, nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    invoice_prefix = Column(String, default="SP")
    invoice_counter = Column(Integer, default=1)

    subscription = relationship("SubscriptionPlan")
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
