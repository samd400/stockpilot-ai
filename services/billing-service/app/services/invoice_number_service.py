from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text


def generate_invoice_number(db: Session, tenant_id: str, prefix: str = "SP") -> str:
    """Generate unique invoice number atomically: PREFIX-YYYY-000001"""
    year = datetime.utcnow().year
    result = db.execute(
        text("""
            UPDATE tenants SET invoice_counter = invoice_counter + 1
            WHERE id = :tenant_id
            RETURNING invoice_counter, invoice_prefix
        """),
        {"tenant_id": tenant_id}
    ).fetchone()

    if result:
        counter = result[0]
        prefix = result[1] or prefix
    else:
        counter = 1

    db.commit()
    return f"{prefix}-{year}-{str(counter).zfill(6)}"
