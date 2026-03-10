import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserRoleEnum(str, enum.Enum):
    admin = "admin"
    staff = "staff"
    manager = "manager"
    billing_staff = "billing_staff"
    inventory_staff = "inventory_staff"
    crm_staff = "crm_staff"
    viewer = "viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRoleEnum), default=UserRoleEnum.viewer, nullable=False)

    business_name = Column(String(255), nullable=True)
    owner_name = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)

    subscription_plan_id = Column(UUID(as_uuid=True), nullable=True)
    gst_number = Column(String(20), nullable=True)
    pan_number = Column(String(20), nullable=True)
    business_address = Column(String(500), nullable=True)
    subscription_expiry = Column(DateTime, nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    invoice_prefix = Column(String(10), default="SP")
    invoice_counter = Column(Integer, default=1)

    tenant = relationship("Tenant", back_populates="users", foreign_keys=[tenant_id])
