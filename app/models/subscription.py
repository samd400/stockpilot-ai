import uuid
from sqlalchemy import Column, String, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String, unique=True, nullable=False)
    price_monthly = Column(Float, nullable=False)

    max_products = Column(Integer, default=50)
    max_branches = Column(Integer, default=1)
    ai_enabled = Column(String, default="basic")  # none, basic, advanced
