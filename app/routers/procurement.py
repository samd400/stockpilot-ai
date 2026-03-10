"""Procurement Router — supplier management & purchase orders."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel
import uuid

from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user
from app.models.user import User
from app.models.supplier import Supplier
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem, POStatus
from app.models.product import Product
from app.services.procurement_service import (
    create_purchase_order,
    send_purchase_order_to_supplier,
    calculate_reorder_quantity,
)

router = APIRouter(prefix="/procurement", tags=["Procurement"])


# ===== Schemas =====

class SupplierCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    lead_time_days: int = 7
    minimum_order_quantity: int = 1
    preferred: bool = False
    api_endpoint: Optional[str] = None
    currency: str = "INR"


class SupplierResponse(BaseModel):
    id: UUID
    name: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    lead_time_days: int
    minimum_order_quantity: int
    preferred: bool
    currency: str

    class Config:
        from_attributes = True


class POItemCreate(BaseModel):
    product_id: UUID
    quantity: int
    unit_cost: float


class POCreate(BaseModel):
    supplier_id: UUID
    items: List[POItemCreate]
    notes: Optional[str] = None
    currency: str = "INR"


class POResponse(BaseModel):
    id: UUID
    supplier_id: Optional[UUID] = None
    status: str
    total_amount: float
    currency: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ===== Supplier Endpoints =====

@router.post("/suppliers", response_model=SupplierResponse)
def add_supplier(
    data: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new supplier."""
    supplier = Supplier(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        name=data.name,
        contact_person=data.contact_person,
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        address=data.address,
        lead_time_days=data.lead_time_days,
        minimum_order_quantity=data.minimum_order_quantity,
        preferred=data.preferred,
        api_endpoint=data.api_endpoint,
        currency=data.currency,
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/suppliers", response_model=list[SupplierResponse])
def list_suppliers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all suppliers for this tenant."""
    return db.query(Supplier).filter(Supplier.tenant_id == current_user.tenant_id).all()


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    s = db.query(Supplier).filter(Supplier.id == supplier_id, Supplier.tenant_id == current_user.tenant_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return s


# ===== Purchase Order Endpoints =====

@router.post("/purchase-orders", response_model=POResponse)
def create_po(
    data: POCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a purchase order."""
    items = [{"product_id": str(i.product_id), "quantity": i.quantity, "unit_cost": i.unit_cost} for i in data.items]
    po = create_purchase_order(
        db=db,
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.id),
        supplier_id=str(data.supplier_id),
        items=items,
        notes=data.notes,
        currency=data.currency,
    )
    return po


@router.get("/purchase-orders", response_model=list[POResponse])
def list_purchase_orders(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List purchase orders for this tenant."""
    query = db.query(PurchaseOrder).filter(PurchaseOrder.tenant_id == current_user.tenant_id)
    if status:
        query = query.filter(PurchaseOrder.status == status)
    return query.order_by(PurchaseOrder.created_at.desc()).all()


@router.post("/purchase-orders/{po_id}/send")
def send_po(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a purchase order to the supplier."""
    po = db.query(PurchaseOrder).filter(
        PurchaseOrder.id == po_id, PurchaseOrder.tenant_id == current_user.tenant_id
    ).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")
    ok = send_purchase_order_to_supplier(db, po)
    return {"sent": ok, "status": po.status.value if hasattr(po.status, 'value') else po.status}


@router.post("/purchase-orders/{po_id}/fulfill")
def fulfill_po(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark PO as fulfilled and update product stock."""
    po = db.query(PurchaseOrder).filter(
        PurchaseOrder.id == po_id, PurchaseOrder.tenant_id == current_user.tenant_id
    ).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")

    for item in po.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.stock_quantity += item.quantity

    po.status = POStatus.FULFILLED
    db.commit()
    return {"message": "PO fulfilled and stock updated"}


@router.get("/reorder-analysis")
def reorder_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze all products and return reorder recommendations."""
    products = db.query(Product).filter(Product.tenant_id == current_user.tenant_id).all()
    results = [calculate_reorder_quantity(db, p) for p in products]
    return {"products": results, "needs_reorder": [r for r in results if r["needs_reorder"]]}
