"""Purchase Order management — ordering stock from suppliers."""
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_inventory_role, require_any_role
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.models.product import Product

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])


def _gen_po_number(db: Session, tenant_id: str) -> str:
    count = db.query(PurchaseOrder).filter(PurchaseOrder.tenant_id == tenant_id).count()
    return f"PO-{count + 1:05d}"


@router.get("/")
def list_pos(status: Optional[str] = None, skip: int = 0, limit: int = 50,
             db: Session = Depends(get_db), user: Dict = Depends(require_any_role)):
    q = db.query(PurchaseOrder).filter(PurchaseOrder.tenant_id == user["tenant_id"])
    if status:
        q = q.filter(PurchaseOrder.status == status)
    pos = q.order_by(PurchaseOrder.created_at.desc()).offset(skip).limit(limit).all()
    return [_po_dict(po, db) for po in pos]


@router.post("/", status_code=201)
def create_po(payload: Dict[str, Any], db: Session = Depends(get_db),
              user: Dict = Depends(require_inventory_role)):
    items_data = payload.pop("items", [])
    po = PurchaseOrder(
        id=uuid.uuid4(),
        tenant_id=user["tenant_id"],
        created_by=user["user_id"],
        po_number=_gen_po_number(db, user["tenant_id"]),
        supplier_id=payload.get("supplier_id"),
        branch_id=payload.get("branch_id"),
        currency=payload.get("currency", "INR"),
        notes=payload.get("notes"),
    )
    db.add(po)

    subtotal = 0.0
    tax_total = 0.0
    for item_data in items_data:
        product = db.query(Product).filter(
            Product.id == item_data["product_id"], Product.tenant_id == user["tenant_id"]
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item_data['product_id']} not found")

        qty = item_data.get("ordered_qty", 0)
        cost = item_data.get("unit_cost", product.purchase_price or 0)
        tax_rate = item_data.get("tax_rate", 0)
        total_cost = qty * cost * (1 + tax_rate / 100)

        po_item = PurchaseOrderItem(
            id=uuid.uuid4(),
            purchase_order_id=po.id,
            product_id=product.id,
            product_name=product.product_name,
            sku=product.sku,
            ordered_qty=qty,
            received_qty=0,
            unit_cost=cost,
            tax_rate=tax_rate,
            total_cost=total_cost,
        )
        db.add(po_item)
        subtotal += qty * cost
        tax_total += total_cost - (qty * cost)

    po.subtotal = round(subtotal, 2)
    po.tax_amount = round(tax_total, 2)
    po.total_amount = round(subtotal + tax_total, 2)
    db.commit()
    db.refresh(po)
    return _po_dict(po, db)


@router.get("/{po_id}")
def get_po(po_id: str, db: Session = Depends(get_db), user: Dict = Depends(require_any_role)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id, PurchaseOrder.tenant_id == user["tenant_id"]).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return _po_dict(po, db)


@router.post("/{po_id}/receive")
def receive_po(po_id: str, payload: Dict[str, Any], db: Session = Depends(get_db),
               user: Dict = Depends(require_inventory_role)):
    """Mark items as received and update product stock."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id, PurchaseOrder.tenant_id == user["tenant_id"]).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if po.status == "received":
        raise HTTPException(status_code=400, detail="PO already fully received")

    received_items = payload.get("items", [])
    for recv in received_items:
        po_item = db.query(PurchaseOrderItem).filter(
            PurchaseOrderItem.purchase_order_id == po_id,
            PurchaseOrderItem.product_id == recv["product_id"]
        ).first()
        if not po_item:
            continue

        qty = recv.get("received_qty", 0)
        po_item.received_qty = min(po_item.ordered_qty, po_item.received_qty + qty)

        # Update product stock
        product = db.query(Product).filter(Product.id == po_item.product_id).first()
        if product:
            product.stock_quantity += qty
            if recv.get("unit_cost"):
                product.purchase_price = recv["unit_cost"]  # Update with actual received cost

    # Update PO status
    items = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.purchase_order_id == po_id).all()
    all_received = all(i.received_qty >= i.ordered_qty for i in items)
    any_received = any(i.received_qty > 0 for i in items)
    po.status = "received" if all_received else ("partial" if any_received else po.status)
    po.received_at = datetime.utcnow() if all_received else po.received_at

    db.commit()
    return {"message": f"PO updated — status: {po.status}", "po_number": po.po_number}


@router.patch("/{po_id}/status")
def update_po_status(po_id: str, payload: Dict[str, Any], db: Session = Depends(get_db),
                     user: Dict = Depends(require_inventory_role)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id, PurchaseOrder.tenant_id == user["tenant_id"]).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    valid_statuses = {"draft", "sent", "partial", "received", "cancelled"}
    new_status = payload.get("status")
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    po.status = new_status
    db.commit()
    return {"message": f"PO status updated to {new_status}"}


def _po_dict(po: PurchaseOrder, db: Session) -> Dict:
    items = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.purchase_order_id == po.id).all()
    return {
        "id": str(po.id), "po_number": po.po_number, "status": po.status,
        "supplier_id": str(po.supplier_id) if po.supplier_id else None,
        "branch_id": str(po.branch_id) if po.branch_id else None,
        "currency": po.currency, "subtotal": po.subtotal,
        "tax_amount": po.tax_amount, "total_amount": po.total_amount,
        "expected_delivery": po.expected_delivery.isoformat() if po.expected_delivery else None,
        "received_at": po.received_at.isoformat() if po.received_at else None,
        "created_at": po.created_at.isoformat(),
        "items": [
            {
                "product_id": str(i.product_id), "product_name": i.product_name, "sku": i.sku,
                "ordered_qty": i.ordered_qty, "received_qty": i.received_qty,
                "unit_cost": i.unit_cost, "tax_rate": i.tax_rate, "total_cost": i.total_cost,
            }
            for i in items
        ],
    }
