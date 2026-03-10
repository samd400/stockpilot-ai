import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, func, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class RevenueMetrics(Base):
    __tablename__ = "revenue_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Monthly Recurring Revenue
    mrr = Column(Float, default=0.0)
    
    # Annual Recurring Revenue
    arr = Column(Float, default=0.0)
    
    # Churn rate
    churn_rate = Column(Float, default=0.0)
    
    # Customer acquisition cost
    cac = Column(Float, default=0.0)
    
    # Lifetime value
    ltv = Column(Float, default=0.0)
    
    # Total active subscriptions
    active_subscriptions = Column(String, default="0")
    
    # Total revenue
    total_revenue = Column(Float, default=0.0)
    
    # Calculated for period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
