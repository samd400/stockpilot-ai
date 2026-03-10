from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
from uuid import UUID

from fastapi.responses import StreamingResponse

from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.product import Product
from app.schemas.invoice import InvoiceCreate, InvoiceResponse
from app.services.pdf_service import generate_invoice_pdf
from app.services.invoice_number_service import generate_invoice_number
from app.tasks.notification_tasks import send_sms_task
from datetime import datetime

router = APIRouter(prefix="/invoices", tags=["Invoices"])


# =====================================================
# CREATE INVOICE (WITH WARRANTY + SMS SUPPORT)
# =====================================================
@router.post("/", response_model=InvoiceResponse)
def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Generate Invoice Number
    invoice_number = generate_invoice_number(db, current_user.id)

    total_amount = 0

    new_invoice = Invoice(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        invoice_number=invoice_number,
        user_id=current_user.id,
        customer_name=invoice_data.customer_name,
        customer_phone=invoice_data.customer_phone,
        total_amount=0
    )

    db.add(new_invoice)
    db.flush()

    for item in invoice_data.items:

        product = db.query(Product).filter(
            Product.id == item.product_id,
            Product.user_id == current_user.id
        ).first()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        if product.stock_quantity < item.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")

        # GST Calculation
        taxable_value = product.selling_price * item.quantity
        gst_percentage = product.gst_percentage or 0

        gst_amount = taxable_value * (gst_percentage / 100)
        cgst = gst_amount / 2
        sgst = gst_amount / 2

        line_total = taxable_value + gst_amount
        total_amount += line_total

        product.stock_quantity -= item.quantity

        warranty_expiry = None
        if product.warranty_months and product.warranty_months > 0:
            warranty_expiry = datetime.utcnow() + timedelta(
                days=product.warranty_months * 30
            )

        invoice_item = InvoiceItem(
            id=uuid.uuid4(),
            invoice_id=new_invoice.id,
            product_id=product.id,
            quantity=item.quantity,
            price_per_unit=product.selling_price,
            warranty_expiry_date=warranty_expiry,
            gst_percentage=gst_percentage,
            cgst_amount=cgst,
            sgst_amount=sgst
        )

        db.add(invoice_item)

    new_invoice.total_amount = total_amount

    db.commit()
    db.refresh(new_invoice)

    # Async SMS
    try:
        if new_invoice.customer_phone:
            send_sms_task.delay(
                new_invoice.customer_phone,
                f"Thank you for shopping with us. "
                f"Invoice No {new_invoice.invoice_number}. "
                f"Total ₹{new_invoice.total_amount}"
            )
    except Exception:
        pass

    return new_invoice



# =====================================================
# WARRANTY LOOKUP
# =====================================================
@router.get("/warranty/{phone}")
def get_warranty_by_phone(
    phone: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):

    results = db.query(
        InvoiceItem,
        Invoice.customer_name,
        Invoice.customer_phone,
        Product.product_name
    ).join(
        Invoice, Invoice.id == InvoiceItem.invoice_id
    ).join(
        Product, Product.id == InvoiceItem.product_id
    ).filter(
        Invoice.user_id == current_user.id,
        Invoice.customer_phone == phone
    ).all()

    response = []

    for item, customer_name, customer_phone, product_name in results:
        response.append({
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "product_name": product_name,
            "warranty_expiry_date": item.warranty_expiry_date
        })

    return response


# =====================================================
# DOWNLOAD PDF
# =====================================================
@router.get("/{invoice_id}/pdf")
def download_invoice_pdf(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):

    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id
    ).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    items = db.query(InvoiceItem).filter(
        InvoiceItem.invoice_id == invoice_id
    ).all()

    pdf_buffer = generate_invoice_pdf(invoice, items)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=invoice_{invoice_id}.pdf"
        }
    )
