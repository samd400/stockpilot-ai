import uuid
from sqlalchemy import Column, String, Float, Integer, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)  # Free, Starter, Pro, Enterprise
    price = Column(Float, default=0)
    billing_cycle = Column(String, default="monthly")  # monthly, yearly
    max_products = Column(Integer, default=10)
    max_invoices_per_month = Column(Integer, default=50)
    max_users = Column(Integer, default=2)
    max_branches = Column(Integer, default=1)
    features = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
