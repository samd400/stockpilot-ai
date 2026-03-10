"""Serialized device & IMEI tracking for electronics retailers."""
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_inventory_role, require_any_role
from app.models.device import Device, RMA

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/devices", tags=["Devices & IMEI"])


@router.get("/")
def list_devices(product_id: Optional[str] = None, status: Optional[str] = None,
                 search: Optional[str] = None, skip: int = 0, limit: int = 50,
                 db: Session = Depends(get_db), user: Dict = Depends(require_any_role)):
    q = db.query(Device).filter(Device.tenant_id == user["tenant_id"])
    if product_id:
        q = q.filter(Device.product_id == product_id)
    if status:
        q = q.filter(Device.status == status)
    if search:
        q = q.filter(
            (Device.serial_number.ilike(f"%{search}%")) |
            (Device.imei.ilike(f"%{search}%"))
        )
    devices = q.order_by(Device.created_at.desc()).offset(skip).limit(limit).all()
    return [_device_dict(d) for d in devices]


@router.post("/", status_code=201)
def register_device(payload: Dict[str, Any], db: Session = Depends(get_db),
                    user: Dict = Depends(require_inventory_role)):
    # Check for duplicate serial/IMEI
    if payload.get("serial_number"):
        existing = db.query(Device).filter(
            Device.serial_number == payload["serial_number"],
            Device.tenant_id == user["tenant_id"]
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Serial number {payload['serial_number']} already registered")

    if payload.get("imei"):
        existing = db.query(Device).filter(Device.imei == payload["imei"]).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"IMEI {payload['imei']} already registered")

    device = Device(
        id=uuid.uuid4(), tenant_id=user["tenant_id"],
        **{k: v for k, v in payload.items() if hasattr(Device, k) and k not in ("id", "tenant_id")}
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return _device_dict(device)


@router.get("/search")
def search_by_imei(imei: str = Query(...), db: Session = Depends(get_db),
                   user: Dict = Depends(require_any_role)):
    device = db.query(Device).filter(
        (Device.imei == imei) | (Device.serial_number == imei),
        Device.tenant_id == user["tenant_id"]
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return _device_dict(device)


@router.patch("/{device_id}")
def update_device(device_id: str, payload: Dict[str, Any], db: Session = Depends(get_db),
                  user: Dict = Depends(require_inventory_role)):
    device = db.query(Device).filter(Device.id == device_id, Device.tenant_id == user["tenant_id"]).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    for k, v in payload.items():
        if k not in ("id", "tenant_id") and hasattr(device, k):
            setattr(device, k, v)
    db.commit()
    return _device_dict(device)


# ─── RMA (Returns) ────────────────────────────────────────────────────────────

rma_router = APIRouter(prefix="/rma", tags=["RMA & Returns"])


def _gen_rma_number(db: Session, tenant_id: str) -> str:
    count = db.query(RMA).filter(RMA.tenant_id == tenant_id).count()
    return f"RMA-{count + 1:05d}"


@rma_router.get("/")
def list_rmas(status: Optional[str] = None, skip: int = 0, limit: int = 50,
              db: Session = Depends(get_db), user: Dict = Depends(require_any_role)):
    q = db.query(RMA).filter(RMA.tenant_id == user["tenant_id"])
    if status:
        q = q.filter(RMA.status == status)
    rmas = q.order_by(RMA.created_at.desc()).offset(skip).limit(limit).all()
    return [_rma_dict(r) for r in rmas]


@rma_router.post("/", status_code=201)
def create_rma(payload: Dict[str, Any], db: Session = Depends(get_db),
               user: Dict = Depends(require_inventory_role)):
    rma = RMA(
        id=uuid.uuid4(), tenant_id=user["tenant_id"],
        rma_number=_gen_rma_number(db, user["tenant_id"]),
        product_id=payload["product_id"],
        device_id=payload.get("device_id"),
        customer_name=payload["customer_name"],
        customer_phone=payload.get("customer_phone"),
        reason=payload["reason"],
    )
    db.add(rma)
    db.commit()
    db.refresh(rma)
    return _rma_dict(rma)


@rma_router.patch("/{rma_id}")
def update_rma(rma_id: str, payload: Dict[str, Any], db: Session = Depends(get_db),
               user: Dict = Depends(require_inventory_role)):
    rma = db.query(RMA).filter(RMA.id == rma_id, RMA.tenant_id == user["tenant_id"]).first()
    if not rma:
        raise HTTPException(status_code=404, detail="RMA not found")
    for k, v in payload.items():
        if k not in ("id", "tenant_id") and hasattr(rma, k):
            setattr(rma, k, v)
    if payload.get("status") in ("repaired", "replaced", "closed"):
        rma.resolved_at = datetime.utcnow()
    db.commit()
    return _rma_dict(rma)


def _device_dict(d: Device) -> Dict:
    return {
        "id": str(d.id), "product_id": str(d.product_id), "serial_number": d.serial_number,
        "imei": d.imei, "imei2": d.imei2, "mac_address": d.mac_address, "status": d.status,
        "invoice_id": str(d.invoice_id) if d.invoice_id else None,
        "customer_name": d.customer_name, "warranty_months": d.warranty_months,
        "warranty_expiry": d.warranty_expiry.isoformat() if d.warranty_expiry else None,
        "created_at": d.created_at.isoformat(),
    }


def _rma_dict(r: RMA) -> Dict:
    return {
        "id": str(r.id), "rma_number": r.rma_number, "status": r.status,
        "product_id": str(r.product_id),
        "device_id": str(r.device_id) if r.device_id else None,
        "customer_name": r.customer_name, "customer_phone": r.customer_phone,
        "reason": r.reason, "resolution": r.resolution,
        "received_at": r.received_at.isoformat(), "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
    }
