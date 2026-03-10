from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user
from app.models.user import User
from app.schemas.purchase import SupplierCreate, Supplier, PurchaseOrderCreate, PurchaseOrder, PurchaseOrderStatusUpdate
from app.services import purchase_service

router = APIRouter(prefix="/purchases", tags=["Purchases"])

# =====================================================
# Supplier Endpoints
# =====================================================
@router.post("/suppliers", response_model=Supplier)
def create_supplier(
    supplier: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return purchase_service.create_supplier(db, current_user, supplier)

@router.get("/suppliers", response_model=List[Supplier])
def get_suppliers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return purchase_service.get_suppliers(db, current_user)

# =====================================================
# Purchase Order Endpoints
# =====================================================
@router.post("/purchase-orders", response_model=PurchaseOrder)
def create_purchase_order(
    order: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return purchase_service.create_purchase_order(db, current_user, order)

@router.get("/purchase-orders", response_model=List[PurchaseOrder])
def get_purchase_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return purchase_service.get_purchase_orders(db, current_user)

@router.get("/purchase-orders/{order_id}", response_model=PurchaseOrder)
def get_purchase_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return purchase_service.get_purchase_order(db, current_user, order_id)

@router.put("/purchase-orders/{order_id}/status", response_model=PurchaseOrder)
def update_purchase_order_status(
    order_id: str,
    status_update: PurchaseOrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return purchase_service.update_purchase_order_status(db, current_user, order_id, status_update)

