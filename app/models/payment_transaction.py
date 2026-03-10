import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, func, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class PaymentGatewayType(str, enum.Enum):
    STRIPE = "STRIPE"
    RAZORPAY = "RAZORPAY"
    PAYTABS = "PAYTABS"
    MANUAL = "MANUAL"


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Transaction details
    amount = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    
    # Gateway info
    gateway = Column(Enum(PaymentGatewayType), nullable=False)
    gateway_transaction_id = Column(String, nullable=True, unique=True)
    
    # Related entities
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("user_subscriptions.id"), nullable=True)
    
    status = Column(String, default="PENDING")  # PENDING, SUCCESS, FAILED, REFUNDED
    
    # Metadata
    description = Column(String, nullable=True)
    payment_metadata = Column(String, nullable=True)  # JSON string
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User")
    invoice = relationship("Invoice")
    subscription = relationship("UserSubscription")
