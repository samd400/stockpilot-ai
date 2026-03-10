import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=False)
    product_name = Column(String, nullable=False)
    product_sku = Column(String, nullable=True)

    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    discount_pct = Column(Float, default=0)
    line_total = Column(Float, nullable=False, default=0)

    gst_percentage = Column(Float, nullable=True)
    cgst_amount = Column(Float, nullable=True)
    sgst_amount = Column(Float, nullable=True)
    igst_amount = Column(Float, nullable=True)
    vat_amount = Column(Float, nullable=True)
    tax_label = Column(String, nullable=True)

    warranty_expiry_date = Column(DateTime, nullable=True)

    invoice = relationship("Invoice", back_populates="items")
