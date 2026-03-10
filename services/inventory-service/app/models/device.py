"""
Serialized device tracking — for electronics retailers.
Tracks individual units by IMEI/Serial number.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    branch_id = Column(UUID(as_uuid=True), nullable=True)

    serial_number = Column(String, nullable=False, index=True)
    imei = Column(String, nullable=True, index=True)       # For mobile devices
    imei2 = Column(String, nullable=True)                  # Dual-SIM second IMEI
    mac_address = Column(String, nullable=True)            # For networking gear

    status = Column(String, default="in_stock")  # in_stock, sold, rma, damaged, transferred

    # Sale info (filled when sold)
    invoice_id = Column(UUID(as_uuid=True), nullable=True)
    sold_at = Column(DateTime, nullable=True)
    customer_name = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)

    # Warranty
    warranty_months = Column(String, default="12")
    warranty_expiry = Column(DateTime, nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RMA(Base):
    """Return Merchandise Authorization — warranty/return tracking."""
    __tablename__ = "rmas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    device_id = Column(UUID(as_uuid=True), nullable=True)
    product_id = Column(UUID(as_uuid=True), nullable=False)

    rma_number = Column(String, nullable=False, unique=True)
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String, nullable=True)
    reason = Column(Text, nullable=False)
    status = Column(String, default="open")  # open, in_repair, repaired, replaced, closed, rejected
    resolution = Column(Text, nullable=True)

    received_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
