import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, func, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class BranchInventory(Base):
    __tablename__ = "branch_inventory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    
    quantity = Column(Integer, default=0)
    reorder_level = Column(Integer, default=10)
    last_stock_check = Column(DateTime, default=func.now())
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    branch = relationship("Branch", back_populates="inventory")
    product = relationship("Product")
