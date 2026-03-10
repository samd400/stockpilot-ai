import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, func, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class DynamicPrice(Base):
    __tablename__ = "dynamic_prices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    
    base_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    
    # Pricing factors
    demand_multiplier = Column(Float, default=1.0)  # Based on sales velocity
    stock_multiplier = Column(Float, default=1.0)  # Based on inventory levels
    seasonality_multiplier = Column(Float, default=1.0)  # Based on season
    competitor_multiplier = Column(Float, default=1.0)  # Based on market
    
    min_price = Column(Float, nullable=False)
    max_price = Column(Float, nullable=False)
    
    last_updated = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

    user = relationship("User")
    product = relationship("Product")
