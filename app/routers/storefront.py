"""
Public Storefront API — No authentication required.
Used by tenant storefronts to display products and create orders.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
import uuid

from app.core.dependencies import get_db
from app.models.tenant import Tenant
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.schemas.order import OrderCreate, OrderResponse
from app.services.tax_engine import calculate_tax

router = APIRouter(prefix="/public", tags=["Public Storefront"])


def _get_tenant_by_subdomain(subdomain: str, db: Session) -> Tenant:
    tenant = db.query(Tenant).filter(
        Tenant.subdomain == subdomain,
        Tenant.is_active == True
    ).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Store not found")
    return tenant


@router.get("/store/{subdomain}")
def get_store_info(subdomain: str, db: Session = Depends(get_db)):
    """Get public store info by subdomain."""
    tenant = _get_tenant_by_subdomain(subdomain, db)
    return {
        "name": tenant.name,
        "subdomain": tenant.subdomain,
        "currency": tenant.currency,
        "country_code": tenant.country_code,
        "logo_url": tenant.logo_url,
        "phone": tenant.phone,
        "address": tenant.business_address,
    }


@router.get("/products/{subdomain}")
def list_public_products(
    subdomain: str,
    category: str = None,
    search: str = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List products for a tenant's storefront."""
    tenant = _get_tenant_by_subdomain(subdomain, db)

    query = db.query(Product).filter(
        Product.tenant_id == tenant.id,
        Product.stock_quantity > 0
    )

    if category:
        query = query.filter(Product.category == category)
    if search:
        query = query.filter(Product.product_name.ilike(f"%{search}%"))

    total = query.count()
    products = query.offset(offset).limit(limit).all()

    return {
        "store": tenant.name,
        "currency": tenant.currency,
        "total": total,
        "products": [
            {
                "id": str(p.id),
                "name": p.product_name,
                "sku": p.sku,
                "category": p.category,
                "price": p.selling_price,
                "currency": p.currency,
                "stock": p.stock_quantity,
                "unit": p.unit,
                "product_type": p.product_type,
                "brand": p.brand,
            }
            for p in products
        ]
    }


@router.get("/products/{subdomain}/{product_id}")
def get_public_product(
    subdomain: str,
    product_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a single product detail."""
    tenant = _get_tenant_by_subdomain(subdomain, db)
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.tenant_id == tenant.id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Calculate tax for display
    tax_result = calculate_tax(
        tenant.tax_region, product.selling_price,
        product.gst_percentage, product.tax_exempt,
        country_code=tenant.country_code
    )

    return {
        "id": str(product.id),
        "name": product.product_name,
        "sku": product.sku,
        "category": product.category,
        "brand": product.brand,
        "price": product.selling_price,
        "currency": product.currency,
        "stock": product.stock_quantity,
        "unit": product.unit,
        "product_type": product.product_type,
        "warranty_months": product.warranty_months,
        "tax": {
            "rate": tax_result.tax_rate,
            "amount": tax_result.tax_amount,
            "label": tax_result.tax_label,
        },
        "price_with_tax": round(product.selling_price + tax_result.tax_amount, 2),
    }


@router.post("/orders/{subdomain}")
def create_public_order(
    subdomain: str,
    order_data: OrderCreate,
    db: Session = Depends(get_db)
):
    """Create an order from the storefront (no auth required)."""
    tenant = _get_tenant_by_subdomain(subdomain, db)
    tenant_id = tenant.id

    new_order = Order(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        customer_name=order_data.customer_name,
        customer_email=order_data.customer_email,
        customer_phone=order_data.customer_phone,
        shipping_address=order_data.shipping_address,
        customer_id=order_data.customer_id,
        notes=order_data.notes,
        currency=tenant.currency,
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
            raise HTTPException(status_code=404, detail=f"Product not found")
        if product.stock_quantity < item_data.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.product_name}")

        unit_price = item_data.unit_price or product.selling_price
        tax_result = calculate_tax(
            tenant.tax_region, unit_price * item_data.quantity,
            product.gst_percentage, product.tax_exempt,
            country_code=tenant.country_code
        )

        line_total = (unit_price * item_data.quantity) + tax_result.tax_amount

        order_item = OrderItem(
            id=uuid.uuid4(),
            order_id=new_order.id,
            product_id=product.id,
            quantity=item_data.quantity,
            unit_price=unit_price,
            tax_percentage=tax_result.tax_rate,
            total=line_total,
        )
        db.add(order_item)

        # Reduce stock
        product.stock_quantity -= item_data.quantity
        subtotal += unit_price * item_data.quantity
        total_tax += tax_result.tax_amount

    new_order.subtotal = subtotal
    new_order.tax = total_tax
    new_order.total = subtotal + total_tax

    # Auto-create invoice
    from app.services.invoice_number_service import generate_invoice_number
    owner = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    invoice = Invoice(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        invoice_number=f"{tenant.invoice_prefix}-{tenant.invoice_counter:05d}",
        user_id=tenant.owner_user_id,
        customer_name=order_data.customer_name,
        customer_phone=order_data.customer_phone,
        currency=tenant.currency,
        subtotal=subtotal,
        tax=total_tax,
        gst_amount=total_tax,
        total_amount=new_order.total,
        region=tenant.tax_region,
        payment_status="UNPAID",
        amount_due=new_order.total,
    )
    db.add(invoice)
    db.flush()

    # Increment counter
    tenant.invoice_counter += 1
    new_order.invoice_id = invoice.id

    db.commit()
    db.refresh(new_order)

    return {
        "order_id": str(new_order.id),
        "invoice_number": invoice.invoice_number,
        "total": new_order.total,
        "currency": new_order.currency,
        "status": new_order.status.value,
        "message": "Order placed successfully",
    }


@router.get("/categories/{subdomain}")
def get_store_categories(subdomain: str, db: Session = Depends(get_db)):
    """Get all product categories for a store."""
    tenant = _get_tenant_by_subdomain(subdomain, db)

    categories = db.query(Product.category).filter(
        Product.tenant_id == tenant.id,
        Product.category.isnot(None)
    ).distinct().all()

    return {"categories": [c[0] for c in categories if c[0]]}
