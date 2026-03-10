import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, func, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class InventoryHealthStatus(str, enum.Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    CRITICAL = "CRITICAL"


class InventoryHealth(Base):
    __tablename__ = "inventory_health"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    
    # Health metrics
    turnover_ratio = Column(Float, default=0.0)  # Sales / Average Inventory
    stock_out_frequency = Column(Float, default=0.0)  # Times out of stock in 30 days
    dead_stock_percentage = Column(Float, default=0.0)  # % of inventory not sold in 90 days
    carrying_cost_ratio = Column(Float, default=0.0)  # Carrying cost / Total inventory value
    
    health_score = Column(Float, default=0.0)  # 0-100
    status = Column(Enum(InventoryHealthStatus), default=InventoryHealthStatus.FAIR)
    
    recommendations = Column(String, nullable=True)  # JSON string with recommendations
    
    calculated_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User")
    product = relationship("Product")
