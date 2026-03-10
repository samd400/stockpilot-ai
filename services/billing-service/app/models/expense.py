import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    category = Column(String, default="other")  # rent, salary, utilities, supplies, marketing, other
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="INR")
    description = Column(String, nullable=True)
    expense_date = Column(DateTime, default=datetime.utcnow)
    receipt_url = Column(String, nullable=True)
    reference_number = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
