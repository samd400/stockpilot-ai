"""RMA (Return Merchandise Authorization) model — returns & warranty claims."""

import uuid
import enum
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, Float, Enum, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class RMAStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RECEIVED = "RECEIVED"
    REFUNDED = "REFUNDED"
    REPLACED = "REPLACED"
    CLOSED = "CLOSED"


class RMA(Base):
    __tablename__ = "rmas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)

    quantity = Column(Integer, default=1)
    status = Column(Enum(RMAStatus), default=RMAStatus.REQUESTED)
    reason = Column(Text, nullable=False)
    resolution = Column(String, nullable=True)  # refund, replace, repair
    refund_amount = Column(Float, nullable=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    product = relationship("Product")
    invoice = relationship("Invoice")
