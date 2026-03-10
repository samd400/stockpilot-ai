import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=True)
    invoice_id = Column(UUID(as_uuid=True), nullable=True)
    gateway = Column(String(50), nullable=False)  # stripe, razorpay, paytabs, cash, upi
    gateway_order_id = Column(String, nullable=True)
    gateway_payment_id = Column(String, nullable=True)
    gateway_signature = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="INR")
    status = Column(String, default="created")  # created, authorized, captured, failed, refunded
    raw_response = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
