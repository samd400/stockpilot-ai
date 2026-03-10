from sqlalchemy.orm import Session
from app.models.user import User
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentStatusUpdate
from app.models.payment import PaymentStatus
from uuid import UUID

def create_payment(db: Session, current_user: User, payment: PaymentCreate) -> Payment:
    invoice = db.query(Invoice).filter(Invoice.id == payment.invoice_id, Invoice.user_id == current_user.id).first()
    if not invoice:
        raise ValueError("Invoice not found")

    db_payment = Payment(
        invoice_id=payment.invoice_id,
        amount=payment.amount,
        mode=payment.mode,
        transaction_id=payment.transaction_id,
        status=PaymentStatus.COMPLETED,
        user_id=current_user.id
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

def get_payments_for_invoice(db: Session, current_user: User, invoice_id: UUID):
    return db.query(Payment).filter(Payment.invoice_id == invoice_id, Payment.user_id == current_user.id).all()

def update_payment_status(db: Session, current_user: User, payment_id: UUID, status_update: PaymentStatusUpdate) -> Payment:
    db_payment = db.query(Payment).filter(Payment.id == payment_id, Payment.user_id == current_user.id).first()
    if not db_payment:
        raise ValueError("Payment not found")
    
    db_payment.status = status_update.status
    db.commit()
    db.refresh(db_payment)
    return db_payment

def get_all_payments(db: Session, current_user: User):
    return db.query(Payment).filter(Payment.user_id == current_user.id).all()
