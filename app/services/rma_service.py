"""RMA Service — return merchandise authorization, approvals, and inventory updates."""

import uuid
import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.models.rma import RMA, RMAStatus
from app.models.product import Product
from app.models.inventory import Inventory
from app.services.procurement_service import log_agent_audit

logger = logging.getLogger(__name__)


def create_rma(
    db: Session,
    tenant_id: str,
    product_id: str,
    reason: str,
    quantity: int = 1,
    invoice_id: str = None,
    order_id: str = None,
) -> RMA:
    """Create a return merchandise authorization request."""
    rma = RMA(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        product_id=product_id,
        invoice_id=invoice_id,
        order_id=order_id,
        quantity=quantity,
        reason=reason,
        status=RMAStatus.REQUESTED,
    )
    db.add(rma)
    db.commit()
    db.refresh(rma)

    log_agent_audit(db, tenant_id, "rma_service", "rma_created",
                    input_data={"product_id": product_id, "quantity": quantity},
                    output_data={"rma_id": str(rma.id)}, status="success")
    return rma


def approve_rma(db: Session, tenant_id: str, rma_id: str, resolution: str = "refund") -> Dict:
    """Approve an RMA and set resolution."""
    rma = db.query(RMA).filter(RMA.id == rma_id, RMA.tenant_id == tenant_id).first()
    if not rma:
        return {"error": "RMA not found"}

    if rma.status != RMAStatus.REQUESTED:
        return {"error": f"Cannot approve RMA in {rma.status.value} status"}

    rma.status = RMAStatus.APPROVED
    rma.resolution = resolution
    db.commit()

    return {"rma_id": str(rma.id), "status": "APPROVED", "resolution": resolution}


def reject_rma(db: Session, tenant_id: str, rma_id: str, reason: str = "") -> Dict:
    """Reject an RMA request."""
    rma = db.query(RMA).filter(RMA.id == rma_id, RMA.tenant_id == tenant_id).first()
    if not rma:
        return {"error": "RMA not found"}
    rma.status = RMAStatus.REJECTED
    db.commit()
    return {"rma_id": str(rma.id), "status": "REJECTED"}


def update_inventory_on_return(db: Session, tenant_id: str, rma_id: str) -> Dict:
    """Add returned items back to inventory after receiving them."""
    rma = db.query(RMA).filter(RMA.id == rma_id, RMA.tenant_id == tenant_id).first()
    if not rma:
        return {"error": "RMA not found"}
    if rma.status != RMAStatus.APPROVED:
        return {"error": "RMA must be APPROVED before receiving return"}

    product = db.query(Product).filter(Product.id == rma.product_id).first()
    if product:
        product.stock_quantity += rma.quantity

    rma.status = RMAStatus.RECEIVED
    db.commit()

    log_agent_audit(db, tenant_id, "rma_service", "return_received",
                    input_data={"rma_id": str(rma_id)},
                    output_data={"product_id": str(rma.product_id), "qty_returned": rma.quantity},
                    status="success")

    return {
        "rma_id": str(rma.id),
        "status": "RECEIVED",
        "product_id": str(rma.product_id),
        "quantity_returned": rma.quantity,
    }
