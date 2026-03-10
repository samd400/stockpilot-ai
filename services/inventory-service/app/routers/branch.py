"""Branch management — multi-location stock operations."""
import uuid
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_inventory_role, require_any_role
from app.models.branch import Branch, BranchInventory
from app.models.product import Product

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/branches", tags=["Branches"])


@router.get("/")
def list_branches(db: Session = Depends(get_db), user: Dict = Depends(require_any_role)):
    branches = db.query(Branch).filter(
        Branch.tenant_id == user["tenant_id"], Branch.is_active == True
    ).all()
    return [_branch_dict(b) for b in branches]


@router.post("/", status_code=201)
def create_branch(payload: Dict[str, Any], db: Session = Depends(get_db),
                  user: Dict = Depends(require_inventory_role)):
    branch = Branch(
        id=uuid.uuid4(), tenant_id=user["tenant_id"],
        **{k: v for k, v in payload.items() if hasattr(Branch, k) and k not in ("id", "tenant_id")}
    )
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return _branch_dict(branch)


@router.get("/{branch_id}")
def get_branch(branch_id: str, db: Session = Depends(get_db), user: Dict = Depends(require_any_role)):
    branch = db.query(Branch).filter(Branch.id == branch_id, Branch.tenant_id == user["tenant_id"]).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    return _branch_dict(branch)


@router.patch("/{branch_id}")
def update_branch(branch_id: str, payload: Dict[str, Any], db: Session = Depends(get_db),
                  user: Dict = Depends(require_inventory_role)):
    branch = db.query(Branch).filter(Branch.id == branch_id, Branch.tenant_id == user["tenant_id"]).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    for k, v in payload.items():
        if k not in ("id", "tenant_id") and hasattr(branch, k):
            setattr(branch, k, v)
    db.commit()
    return _branch_dict(branch)


@router.get("/{branch_id}/inventory")
def get_branch_inventory(branch_id: str, db: Session = Depends(get_db),
                          user: Dict = Depends(require_any_role)):
    """Get all stock levels for a specific branch."""
    branch = db.query(Branch).filter(Branch.id == branch_id, Branch.tenant_id == user["tenant_id"]).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    items = db.query(BranchInventory).filter(
        BranchInventory.branch_id == branch_id,
        BranchInventory.tenant_id == user["tenant_id"]
    ).all()

    result = []
    for item in items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        result.append({
            "product_id": str(item.product_id),
            "product_name": product.product_name if product else "Unknown",
            "sku": product.sku if product else None,
            "quantity": item.quantity,
            "reorder_level": item.reorder_level,
            "bin_location": item.bin_location,
        })
    return result


@router.post("/{branch_id}/inventory/adjust")
def adjust_branch_stock(branch_id: str, payload: Dict[str, Any], db: Session = Depends(get_db),
                         user: Dict = Depends(require_inventory_role)):
    """Adjust stock quantity for a product at a branch."""
    product_id = payload.get("product_id")
    quantity = payload.get("quantity", 0)

    bi = db.query(BranchInventory).filter(
        BranchInventory.branch_id == branch_id,
        BranchInventory.product_id == product_id,
        BranchInventory.tenant_id == user["tenant_id"]
    ).first()

    if not bi:
        bi = BranchInventory(
            id=uuid.uuid4(),
            tenant_id=user["tenant_id"],
            branch_id=branch_id,
            product_id=product_id,
            quantity=str(quantity),
            reorder_level=str(payload.get("reorder_level", 10)),
            bin_location=payload.get("bin_location"),
        )
        db.add(bi)
    else:
        bi.quantity = str(quantity)
        if payload.get("bin_location"):
            bi.bin_location = payload["bin_location"]
    db.commit()
    return {"message": "Branch inventory updated", "quantity": quantity}


def _branch_dict(b: Branch) -> Dict:
    return {
        "id": str(b.id), "name": b.name, "code": b.code, "city": b.city,
        "country": b.country, "is_main": b.is_main, "is_active": b.is_active,
        "phone": b.phone, "email": b.email, "address": b.address,
        "created_at": b.created_at.isoformat(),
    }
