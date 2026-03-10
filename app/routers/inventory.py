from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
import uuid

from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user
from app.models.user import User
from app.models.inventory import Inventory
from app.models.location import Location
from app.schemas.inventory import (
    InventoryCreate, InventoryUpdate, InventoryResponse,
    LocationCreate, LocationResponse
)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


# ===== Location / Warehouse Endpoints =====

@router.post("/locations", response_model=LocationResponse)
def create_location(
    loc: LocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_loc = Location(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        name=loc.name,
        location_type=loc.location_type,
        address=loc.address,
        city=loc.city,
        state=loc.state,
        country=loc.country,
        pincode=loc.pincode,
        phone=loc.phone,
        is_default=loc.is_default,
    )
    db.add(new_loc)
    db.commit()
    db.refresh(new_loc)
    return new_loc


@router.get("/locations", response_model=list[LocationResponse])
def list_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Location).filter(
        Location.tenant_id == current_user.tenant_id,
        Location.is_active == True
    ).all()


@router.delete("/locations/{location_id}")
def delete_location(
    location_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    loc = db.query(Location).filter(
        Location.id == location_id,
        Location.tenant_id == current_user.tenant_id
    ).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    loc.is_active = False
    db.commit()
    return {"message": "Location deactivated"}


# ===== Inventory Endpoints =====

@router.post("/", response_model=InventoryResponse)
def create_or_update_inventory(
    inv: InventoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create or update inventory for a product at a location."""
    existing = db.query(Inventory).filter(
        Inventory.tenant_id == current_user.tenant_id,
        Inventory.product_id == inv.product_id,
        Inventory.location_id == inv.location_id
    ).first()

    if existing:
        existing.quantity = inv.quantity
        db.commit()
        db.refresh(existing)
        return existing

    new_inv = Inventory(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        product_id=inv.product_id,
        location_id=inv.location_id,
        quantity=inv.quantity,
    )
    db.add(new_inv)
    db.commit()
    db.refresh(new_inv)
    return new_inv


@router.get("/", response_model=list[InventoryResponse])
def list_inventory(
    location_id: UUID = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Inventory).filter(Inventory.tenant_id == current_user.tenant_id)
    if location_id:
        query = query.filter(Inventory.location_id == location_id)
    return query.all()


@router.get("/{product_id}", response_model=list[InventoryResponse])
def get_product_inventory(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get inventory across all locations for a product."""
    return db.query(Inventory).filter(
        Inventory.tenant_id == current_user.tenant_id,
        Inventory.product_id == product_id
    ).all()


@router.put("/{inventory_id}", response_model=InventoryResponse)
def update_inventory(
    inventory_id: UUID,
    update: InventoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inv = db.query(Inventory).filter(
        Inventory.id == inventory_id,
        Inventory.tenant_id == current_user.tenant_id
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory record not found")
    inv.quantity = update.quantity
    db.commit()
    db.refresh(inv)
    return inv
