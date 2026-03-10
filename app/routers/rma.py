"""RMA Router — return merchandise authorization management."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from pydantic import BaseModel

from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user
from app.models.user import User
from app.models.rma import RMA
from app.services.rma_service import create_rma, approve_rma, reject_rma, update_inventory_on_return

router = APIRouter(prefix="/rma", tags=["RMA"])


class RMACreate(BaseModel):
    product_id: UUID
    quantity: int = 1
    reason: str
    invoice_id: Optional[UUID] = None
    order_id: Optional[UUID] = None


class RMAResponse(BaseModel):
    id: UUID
    product_id: UUID
    status: str
    reason: str
    quantity: int
    resolution: Optional[str] = None

    class Config:
        from_attributes = True


@router.post("/", response_model=RMAResponse)
def create_rma_request(
    data: RMACreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new RMA return request."""
    rma = create_rma(
        db=db,
        tenant_id=str(current_user.tenant_id),
        product_id=str(data.product_id),
        reason=data.reason,
        quantity=data.quantity,
        invoice_id=str(data.invoice_id) if data.invoice_id else None,
        order_id=str(data.order_id) if data.order_id else None,
    )
    return rma


@router.get("/", response_model=list[RMAResponse])
def list_rmas(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all RMA requests for this tenant."""
    query = db.query(RMA).filter(RMA.tenant_id == current_user.tenant_id)
    if status:
        query = query.filter(RMA.status == status)
    return query.order_by(RMA.created_at.desc()).all()


@router.post("/{rma_id}/approve")
def approve(
    rma_id: UUID,
    resolution: str = "refund",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve an RMA request."""
    result = approve_rma(db, str(current_user.tenant_id), str(rma_id), resolution)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{rma_id}/reject")
def reject(
    rma_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = reject_rma(db, str(current_user.tenant_id), str(rma_id))
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{rma_id}/receive")
def receive_return(
    rma_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Receive returned items and update inventory."""
    result = update_inventory_on_return(db, str(current_user.tenant_id), str(rma_id))
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
