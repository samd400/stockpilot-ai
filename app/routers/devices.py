"""Device pairing & management router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID
import uuid
import secrets
import json

from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user
from app.core.security import create_access_token
from app.models.user import User
from app.models.device import Device, DeviceType, DeviceStatus

router = APIRouter(prefix="/devices", tags=["Devices"])


class DevicePairRequest(BaseModel):
    device_name: str
    device_type: str  # desktop, mobile, pos_terminal
    platform: Optional[str] = None


class DeviceClaimRequest(BaseModel):
    pairing_token: str
    device_metadata: Optional[dict] = None


class DeviceResponse(BaseModel):
    id: UUID
    device_name: str
    device_type: str
    status: str
    is_kiosk: bool

    class Config:
        from_attributes = True


# ===== Pairing Flow =====

@router.post("/pair")
def pair_device(
    data: DevicePairRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Step 1: Admin creates a pairing request. Returns a short-lived pairing token.
    The device will display this as a QR code or manual entry.
    """
    pairing_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    device_type_enum = DeviceType(data.device_type) if data.device_type in [e.value for e in DeviceType] else DeviceType.DESKTOP

    device = Device(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        device_name=data.device_name,
        device_type=device_type_enum,
        platform=data.platform,
        status=DeviceStatus.PENDING,
        pairing_token=pairing_token,
        pairing_expires_at=expires_at,
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    return {
        "device_id": str(device.id),
        "pairing_token": pairing_token,
        "expires_at": expires_at.isoformat(),
    }


@router.post("/claim")
def claim_device(
    data: DeviceClaimRequest,
    db: Session = Depends(get_db),
):
    """
    Step 2: Device claims the pairing token (no auth required — token IS the auth).
    Returns a long-lived device token for API access.
    """
    device = db.query(Device).filter(
        Device.pairing_token == data.pairing_token,
        Device.status == DeviceStatus.PENDING,
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="Invalid or expired pairing token")

    if device.pairing_expires_at and device.pairing_expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Pairing token has expired")

    # Generate long-lived device token
    device_token = create_access_token(
        data={"sub": str(device.id), "tenant_id": str(device.tenant_id), "type": "device"},
        expires_delta=timedelta(days=365),
    )

    device.device_token = device_token
    device.status = DeviceStatus.ACTIVE
    device.pairing_token = None  # Consumed
    device.device_metadata = json.dumps(data.device_metadata) if data.device_metadata else None
    device.last_seen_at = datetime.utcnow()
    db.commit()

    return {
        "device_id": str(device.id),
        "device_token": device_token,
        "tenant_id": str(device.tenant_id),
        "status": "active",
    }


@router.get("/", response_model=list[DeviceResponse])
def list_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all devices for this tenant."""
    return db.query(Device).filter(Device.tenant_id == current_user.tenant_id).all()


@router.post("/{device_id}/revoke")
def revoke_device(
    device_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke a device's access."""
    device = db.query(Device).filter(
        Device.id == device_id, Device.tenant_id == current_user.tenant_id
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.status = DeviceStatus.REVOKED
    device.device_token = None
    db.commit()
    return {"message": "Device revoked", "device_id": str(device_id)}


@router.post("/{device_id}/kiosk")
def toggle_kiosk(
    device_id: UUID,
    enable: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enable/disable kiosk mode for a device."""
    device = db.query(Device).filter(
        Device.id == device_id, Device.tenant_id == current_user.tenant_id
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.is_kiosk = enable
    db.commit()
    return {"device_id": str(device_id), "kiosk": enable}
