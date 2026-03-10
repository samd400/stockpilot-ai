from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime


class InventoryCreate(BaseModel):
    product_id: UUID
    location_id: UUID
    quantity: int = 0


class InventoryUpdate(BaseModel):
    quantity: int


class InventoryResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    product_id: UUID
    location_id: UUID
    quantity: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LocationCreate(BaseModel):
    name: str
    location_type: str = "warehouse"
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None
    is_default: bool = False


class LocationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    location_type: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    is_default: bool
    is_active: bool

    class Config:
        from_attributes = True
