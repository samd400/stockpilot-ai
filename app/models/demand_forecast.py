import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, func, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class DemandForecast(Base):
    __tablename__ = "demand_forecasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    
    # Forecast data
    forecast_date = Column(DateTime, nullable=False)
    predicted_quantity = Column(Integer, nullable=False)
    confidence_level = Column(Float, default=0.0)  # 0-100
    
    # Historical data used
    historical_avg_sales = Column(Float, default=0.0)
    trend = Column(String, nullable=True)  # "UP", "DOWN", "STABLE"
    seasonality_factor = Column(Float, default=1.0)
    
    # Recommendations
    recommended_stock = Column(Integer, nullable=False)
    reorder_urgency = Column(String, default="NORMAL")  # URGENT, HIGH, NORMAL, LOW
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User")
    product = relationship("Product")
