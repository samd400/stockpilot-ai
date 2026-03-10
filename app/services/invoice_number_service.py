from datetime import datetime
from sqlalchemy.orm import Session
from app.models.invoice import Invoice


def generate_invoice_number(db: Session, user_id):

    current_year = datetime.utcnow().year

    last_invoice = db.query(Invoice).filter(
        Invoice.user_id == user_id,
        Invoice.invoice_number.like(f"INV-{current_year}-%")
    ).order_by(Invoice.created_at.desc()).first()

    if not last_invoice:
        return f"INV-{current_year}-0001"

    last_number = int(last_invoice.invoice_number.split("-")[-1])
    new_number = str(last_number + 1).zfill(4)

    return f"INV-{current_year}-{new_number}"
