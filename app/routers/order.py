from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
import uuid

from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user, get_current_tenant_id
from app.models.user import User
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatusEnum
from app.models.product import Product
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from app.services.invoice_number_service import generate_invoice_number

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create order → auto-create invoice → reduce inventory."""
    tenant_id = current_user.tenant_id

    new_order = Order(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        customer_name=order_data.customer_name,
        customer_email=order_data.customer_email,
        customer_phone=order_data.customer_phone,
        shipping_address=order_data.shipping_address,
        customer_id=order_data.customer_id,
        notes=order_data.notes,
    )
    db.add(new_order)
    db.flush()

    subtotal = 0
    total_tax = 0

    for item_data in order_data.items:
        product = db.query(Product).filter(
            Product.id == item_data.product_id,
            Product.tenant_id == tenant_id
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item_data.product_id} not found")
        if product.stock_quantity < item_data.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.product_name}")

        unit_price = item_data.unit_price or product.selling_price
        tax_pct = 0 if product.tax_exempt else (product.gst_percentage or 0)
        line_subtotal = unit_price * item_data.quantity
        line_tax = line_subtotal * (tax_pct / 100)
        line_total = line_subtotal + line_tax

        order_item = OrderItem(
            id=uuid.uuid4(),
            order_id=new_order.id,
            product_id=product.id,
            quantity=item_data.quantity,
            unit_price=unit_price,
            tax_percentage=tax_pct,
            total=line_total,
        )
        db.add(order_item)

        # Reduce inventory
        product.stock_quantity -= item_data.quantity
        subtotal += line_subtotal
        total_tax += line_tax

    new_order.subtotal = subtotal
    new_order.tax = total_tax
    new_order.total = subtotal + total_tax
    new_order.currency = product.currency if product else "INR"

    # Auto-create invoice
    invoice_number = generate_invoice_number(db, current_user.id)
    invoice = Invoice(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        invoice_number=invoice_number,
        user_id=current_user.id,
        customer_id=order_data.customer_id,
        customer_name=order_data.customer_name,
        customer_phone=order_data.customer_phone,
        currency=new_order.currency,
        subtotal=subtotal,
        tax=total_tax,
        gst_amount=total_tax,
        total_amount=new_order.total,
        payment_status="UNPAID",
        amount_due=new_order.total,
    )
    db.add(invoice)
    db.flush()

    # Link items to invoice
    for oi in db.query(OrderItem).filter(OrderItem.order_id == new_order.id).all():
        inv_item = InvoiceItem(
            id=uuid.uuid4(),
            invoice_id=invoice.id,
            product_id=oi.product_id,
            quantity=oi.quantity,
            price_per_unit=oi.unit_price,
            gst_percentage=oi.tax_percentage,
        )
        db.add(inv_item)

    new_order.invoice_id = invoice.id
    db.commit()
    db.refresh(new_order)

    return new_order


@router.get("/", response_model=list[OrderResponse])
def list_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Order).filter(Order.tenant_id == current_user.tenant_id).order_by(Order.created_at.desc()).all()


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.tenant_id == current_user.tenant_id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.put("/{order_id}/status")
def update_order_status(
    order_id: UUID,
    status_data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.tenant_id == current_user.tenant_id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        order.status = OrderStatus(status_data.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status")

    db.commit()
    return {"message": f"Order status updated to {status_data.status}"}
