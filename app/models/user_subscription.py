import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, func, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    DOWNGRADED = "DOWNGRADED"


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Legacy compat
    subscription_plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False)

    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)

    # Billing info
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    renewal_date = Column(DateTime, nullable=False)

    # Payment info
    amount_paid = Column(Float, default=0.0)
    payment_method = Column(String, nullable=True)  # stripe, razorpay, paytabs, manual
    stripe_subscription_id = Column(String, nullable=True)
    razorpay_subscription_id = Column(String, nullable=True)
    paytabs_subscription_id = Column(String, nullable=True)

    auto_renew = Column(String, default="true")

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User")
    plan = relationship("SubscriptionPlan")
