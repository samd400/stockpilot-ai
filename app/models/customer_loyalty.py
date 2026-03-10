import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, func, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class LoyaltyTierType(str, enum.Enum):
    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"


class CustomerLoyalty(Base):
    __tablename__ = "customer_loyalty"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    total_spent = Column(Float, default=0.0)
    loyalty_points = Column(Float, default=0.0)
    tier = Column(Enum(LoyaltyTierType), default=LoyaltyTierType.BRONZE)
    
    # Tier benefits
    discount_percentage = Column(Float, default=0.0)
    points_multiplier = Column(Float, default=1.0)
    
    last_purchase_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    customer = relationship("Customer")
    user = relationship("User")
