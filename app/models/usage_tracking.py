import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, func, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class UsageMetricType(str, enum.Enum):
    API_CALLS = "API_CALLS"
    INVOICES_CREATED = "INVOICES_CREATED"
    PRODUCTS_MANAGED = "PRODUCTS_MANAGED"
    STORAGE_USED = "STORAGE_USED"
    USERS_CREATED = "USERS_CREATED"


class UsageTracking(Base):
    __tablename__ = "usage_tracking"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Legacy compat

    metric_type = Column(Enum(UsageMetricType), nullable=False)
    value = Column(Float, default=0.0)

    # Plan limits
    plan_limit = Column(Float, nullable=True)
    usage_percentage = Column(Float, default=0.0)

    billing_period_start = Column(DateTime, nullable=False)
    billing_period_end = Column(DateTime, nullable=False)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User")
