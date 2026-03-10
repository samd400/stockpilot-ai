"""
CRM Service — Orders router.
Handles customer orders (online/channel orders distinct from POS invoices).
"""
import uuid
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_crm_role, require_any_role
from app.models.order import Order, OrderItem
from app.models.customer import Customer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/")
def list_orders(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    channel: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Dict = Depends(require_any_role),
):
    """List all orders for the tenant with optional filters."""
    q = db.query(Order).filter(Order.tenant_id == user["tenant_id"])
    if status:
        q = q.filter(Order.status == status)
    if customer_id:
        q = q.filter(Order.customer_id == customer_id)
    if channel:
        q = q.filter(Order.channel == channel)
    orders = q.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return [_order_to_dict(o) for o in orders]


@router.get("/{order_id}")
def get_order(order_id: str, db: Session = Depends(get_db),
              user: Dict = Depends(require_any_role)):
    """Get a specific order by ID."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.tenant_id == user["tenant_id"],
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _order_to_dict(order, include_items=True)


@router.post("/")
def create_order(payload: Dict[str, Any], db: Session = Depends(get_db),
                 user: Dict = Depends(require_crm_role)):
    """Create a new order."""
    tenant_id = user["tenant_id"]

    # Validate customer if provided
    customer_id = payload.get("customer_id")
    if customer_id:
        customer = db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.tenant_id == tenant_id,
        ).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

    # Generate order number
    order_count = db.query(Order).filter(Order.tenant_id == tenant_id).count()
    order_number = payload.get("order_number") or f"ORD-{order_count + 1:05d}"

    order = Order(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        customer_id=customer_id,
        order_number=order_number,
        status=payload.get("status", "pending"),
        channel=payload.get("channel", "manual"),
        currency=payload.get("currency", "INR"),
        shipping_address=payload.get("shipping_address"),
        notes=payload.get("notes"),
    )

    # Add line items
    total_amount = 0.0
    for item_data in payload.get("items", []):
        qty = float(item_data.get("quantity", 1))
        price = float(item_data.get("unit_price", 0))
        line_total = qty * price
        total_amount += line_total

        item = OrderItem(
            id=uuid.uuid4(),
            order_id=order.id,
            product_id=item_data.get("product_id"),
            product_name=item_data.get("product_name", ""),
            product_sku=item_data.get("product_sku"),
            quantity=qty,
            unit_price=price,
            line_total=line_total,
        )
        order.items.append(item)

    order.total_amount = payload.get("total_amount", total_amount)

    db.add(order)
    db.commit()
    db.refresh(order)
    logger.info(f"Order {order.order_number} created for tenant {tenant_id}")
    return _order_to_dict(order, include_items=True)


@router.put("/{order_id}/status")
def update_order_status(order_id: str, payload: Dict[str, Any],
                         db: Session = Depends(get_db),
                         user: Dict = Depends(require_crm_role)):
    """Update order status (pending → confirmed → shipped → delivered → cancelled)."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.tenant_id == user["tenant_id"],
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    new_status = payload.get("status")
    valid_statuses = {"pending", "confirmed", "processing", "shipped", "delivered", "cancelled", "returned"}
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    order.status = new_status
    if payload.get("notes"):
        order.notes = payload["notes"]
    db.commit()
    return _order_to_dict(order)


@router.delete("/{order_id}")
def cancel_order(order_id: str, db: Session = Depends(get_db),
                 user: Dict = Depends(require_crm_role)):
    """Cancel an order (sets status to cancelled)."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.tenant_id == user["tenant_id"],
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status in ("delivered", "returned"):
        raise HTTPException(status_code=409, detail="Cannot cancel a delivered order")
    order.status = "cancelled"
    db.commit()
    return {"cancelled": True, "order_number": order.order_number}


def _order_to_dict(order: Order, include_items: bool = False) -> Dict:
    data = {
        "id": str(order.id),
        "order_number": order.order_number,
        "customer_id": str(order.customer_id) if order.customer_id else None,
        "status": order.status,
        "channel": order.channel,
        "total_amount": order.total_amount,
        "currency": order.currency,
        "shipping_address": order.shipping_address,
        "notes": order.notes,
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
    }
    if include_items:
        data["items"] = [
            {
                "id": str(i.id),
                "product_id": str(i.product_id) if i.product_id else None,
                "product_name": i.product_name,
                "product_sku": i.product_sku,
                "quantity": i.quantity,
                "unit_price": i.unit_price,
                "line_total": i.line_total,
            }
            for i in (order.items or [])
        ]
    return data
