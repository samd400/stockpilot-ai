import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.core.database import Base


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String, nullable=False, unique=True)  # Free / Pro / Enterprise
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    billing_cycle = Column(String, default="monthly")  # monthly, yearly

    # Feature limits
    max_products = Column(Integer, default=10)
    max_invoices_per_month = Column(Integer, default=50)
    max_branches = Column(Integer, default=1)
    max_users = Column(Integer, default=1)
    max_locations = Column(Integer, default=1)

    # Features
    gst_compliance = Column(Boolean, default=True)
    pdf_export = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    analytics = Column(Boolean, default=False)
    ai_features = Column(Boolean, default=False)
    multi_branch = Column(Boolean, default=False)
    pos_billing = Column(Boolean, default=False)
    crm_features = Column(Boolean, default=False)
    demand_forecasting = Column(Boolean, default=False)
    dynamic_pricing = Column(Boolean, default=False)
    storefront = Column(Boolean, default=False)
    agents = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
