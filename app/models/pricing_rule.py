"""Pricing Rule model — per-product dynamic pricing configuration."""

import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Float, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class PricingRule(Base):
    __tablename__ = "pricing_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)

    region = Column(String, nullable=True)  # india_gst, gcc_vat, eu_vat
    margin_floor = Column(Float, default=10.0)  # Minimum margin % allowed
    dynamic_enabled = Column(Boolean, default=False)

    recommended_price = Column(Float, nullable=True)
    recommendation_reason = Column(String, nullable=True)

    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now())

    product = relationship("Product")
