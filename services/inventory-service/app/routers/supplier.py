"""Supplier management."""
import uuid
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_inventory_role, require_any_role
from app.models.supplier import Supplier

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.get("/")
def list_suppliers(search: Optional[str] = None, country: Optional[str] = None,
                   skip: int = 0, limit: int = 50,
                   db: Session = Depends(get_db), user: Dict = Depends(require_any_role)):
    q = db.query(Supplier).filter(Supplier.tenant_id == user["tenant_id"], Supplier.is_active == True)
    if search:
        q = q.filter(Supplier.name.ilike(f"%{search}%"))
    if country:
        q = q.filter(Supplier.country == country)
    suppliers = q.offset(skip).limit(limit).all()
    return [_supplier_dict(s) for s in suppliers]


@router.post("/", status_code=201)
def create_supplier(payload: Dict[str, Any], db: Session = Depends(get_db),
                    user: Dict = Depends(require_inventory_role)):
    supplier = Supplier(
        id=uuid.uuid4(), tenant_id=user["tenant_id"],
        **{k: v for k, v in payload.items() if hasattr(Supplier, k) and k not in ("id", "tenant_id")}
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return _supplier_dict(supplier)


@router.get("/{supplier_id}")
def get_supplier(supplier_id: str, db: Session = Depends(get_db), user: Dict = Depends(require_any_role)):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id, Supplier.tenant_id == user["tenant_id"]).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return _supplier_dict(supplier)


@router.patch("/{supplier_id}")
def update_supplier(supplier_id: str, payload: Dict[str, Any], db: Session = Depends(get_db),
                    user: Dict = Depends(require_inventory_role)):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id, Supplier.tenant_id == user["tenant_id"]).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    for k, v in payload.items():
        if k not in ("id", "tenant_id") and hasattr(supplier, k):
            setattr(supplier, k, v)
    db.commit()
    return _supplier_dict(supplier)


@router.delete("/{supplier_id}")
def delete_supplier(supplier_id: str, db: Session = Depends(get_db),
                    user: Dict = Depends(require_inventory_role)):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id, Supplier.tenant_id == user["tenant_id"]).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    supplier.is_active = False
    db.commit()
    return {"message": "Supplier deactivated"}


def _supplier_dict(s: Supplier) -> Dict:
    return {
        "id": str(s.id), "name": s.name, "contact_person": s.contact_person,
        "email": s.email, "phone": s.phone, "country": s.country,
        "gst_number": s.gst_number, "tax_id": s.tax_id,
        "payment_terms_days": s.payment_terms_days, "lead_time_days": s.lead_time_days,
        "rating": s.rating, "is_active": s.is_active,
    }
