from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.core.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    invoice_number = Column(String, unique=True, nullable=False, index=True)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True)

    # Customer info (inline for storefront orders)
    customer_name = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)

    # Amount details
    currency = Column(String(3), default="INR")
    subtotal = Column(Float, default=0)
    tax = Column(Float, default=0)
    gst_amount = Column(Float, default=0)
    total_amount = Column(Float, default=0)

    # Region & tax
    region = Column(String(20), default="india_gst")  # india_gst, gcc_vat, eu_vat

    # Payment tracking
    payment_status = Column(String, default="UNPAID")
    amount_paid = Column(Float, default=0)
    amount_due = Column(Float, default=0)

    # Invoice details
    invoice_type = Column(String, default="SALES")  # SALES, PURCHASE, CREDIT_NOTE
    notes = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("InvoiceItem", back_populates="invoice")
    payments = relationship("Payment", back_populates="invoice")
    customer = relationship("Customer")
