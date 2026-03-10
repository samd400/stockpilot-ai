import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    invoice_number = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    customer_id = Column(UUID(as_uuid=True), nullable=True)
    branch_id = Column(UUID(as_uuid=True), nullable=True)

    # Customer fields
    customer_name = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)
    customer_email = Column(String, nullable=True)
    customer_address = Column(Text, nullable=True)
    customer_city = Column(String, nullable=True)
    customer_state = Column(String, nullable=True)
    customer_country = Column(String(2), nullable=True)

    # Tax IDs (region-specific)
    customer_gstin = Column(String, nullable=True)      # India B2B GST number
    customer_tax_id = Column(String, nullable=True)     # EU VAT / GCC TRN
    supplier_name = Column(String, nullable=True)       # For e-invoices
    supplier_trn = Column(String, nullable=True)        # GCC Tax Registration Number

    # Amounts
    currency = Column(String(3), default="INR")
    subtotal = Column(Float, default=0)
    discount_amount = Column(Float, default=0)
    tax_amount = Column(Float, default=0)               # Total tax aggregate
    cgst_amount = Column(Float, default=0)              # India CGST
    sgst_amount = Column(Float, default=0)              # India SGST
    igst_amount = Column(Float, default=0)              # India IGST
    gst_amount = Column(Float, default=0)               # India total GST (legacy)
    vat_amount = Column(Float, default=0)               # GCC / EU VAT
    total_amount = Column(Float, default=0)

    # Status
    region = Column(String(20), default="india")        # india, gcc, eu
    country_code = Column(String(2), nullable=True)
    status = Column(String, default="draft")            # draft, sent, paid, cancelled, void
    payment_status = Column(String, default="UNPAID")
    amount_paid = Column(Float, default=0)
    amount_due = Column(Float, default=0)

    # e-Invoice (India IRN / GCC ZATCA)
    irn = Column(String, nullable=True)
    e_invoice_status = Column(String, nullable=True)    # generated, submitted, cancelled
    qr_code_data = Column(Text, nullable=True)

    invoice_type = Column(String, default="SALES")
    notes = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice")
