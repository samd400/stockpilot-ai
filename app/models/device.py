"""Device model — tracks paired devices (desktop, mobile, POS terminals)."""

import uuid
import enum
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Enum, Text, func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class DeviceType(str, enum.Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    POS_TERMINAL = "pos_terminal"


class DeviceStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    REVOKED = "revoked"


class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    device_name = Column(String, nullable=False)
    device_type = Column(Enum(DeviceType), nullable=False)
    platform = Column(String, nullable=True)
    status = Column(Enum(DeviceStatus), default=DeviceStatus.PENDING)

    # Pairing
    pairing_token = Column(String, nullable=True, unique=True, index=True)
    pairing_expires_at = Column(DateTime, nullable=True)
    device_token = Column(String, nullable=True, unique=True)  # Long-lived auth token

    device_metadata = Column(Text, nullable=True)  # JSON
    last_seen_at = Column(DateTime, nullable=True)
    is_kiosk = Column(Boolean, default=False)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
