from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from app.models.payment import PaymentStatus, PaymentMode
from app.schemas.customer import Customer

class PaymentCreate(BaseModel):
    invoice_id: UUID
    amount: float
    mode: PaymentMode
    transaction_id: str | None = None

class PaymentResponse(BaseModel):
    id: UUID
    invoice_id: UUID
    amount: float
    status: PaymentStatus
    mode: PaymentMode
    transaction_id: str | None
    created_at: datetime
    customer: Customer

    class Config:
        from_attributes = True

class PaymentStatusUpdate(BaseModel):
    status: PaymentStatus

class PaymentDetails(PaymentResponse):
    pass
