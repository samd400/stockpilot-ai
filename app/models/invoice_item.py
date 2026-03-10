from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.core.database import Base


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)

    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)

    gst_percentage = Column(Float)
    cgst_amount = Column(Float)
    sgst_amount = Column(Float)

    warranty_expiry_date = Column(DateTime, nullable=True)

    # Relationships
    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product")
