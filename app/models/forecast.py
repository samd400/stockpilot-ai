"""Demand Forecast model — stores ML predictions per product."""

import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Float, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)

    horizon_days = Column(Integer, nullable=False, default=30)
    predicted_quantity = Column(Float, nullable=False)
    confidence_low = Column(Float, nullable=True)
    confidence_high = Column(Float, nullable=True)
    model_type = Column(String, default="linear_regression")  # linear_regression, prophet

    created_at = Column(DateTime, default=func.now())

    product = relationship("Product")
