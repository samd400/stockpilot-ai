from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentStatusUpdate
from app.services import payment_service
from typing import List

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/", response_model=PaymentResponse)
def create_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return payment_service.create_payment(db, current_user, payment)

@router.get("/{invoice_id}", response_model=List[PaymentResponse])
def get_payments_for_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return payment_service.get_payments_for_invoice(db, current_user, invoice_id)

@router.put("/{payment_id}/status", response_model=PaymentResponse)
def update_payment_status(
    payment_id: str,
    status_update: PaymentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return payment_service.update_payment_status(db, current_user, payment_id, status_update)
