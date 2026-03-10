from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime


class OrderItemCreate(BaseModel):
    product_id: UUID
    quantity: int
    unit_price: Optional[float] = None  # If None, uses product selling_price


class OrderCreate(BaseModel):
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    shipping_address: Optional[str] = None
    customer_id: Optional[UUID] = None
    items: List[OrderItemCreate]
    notes: Optional[str] = None


class OrderItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    quantity: int
    unit_price: float
    tax_percentage: float
    total: float

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    currency: str
    subtotal: float
    tax: float
    total: float
    status: str
    payment_status: str
    invoice_id: Optional[UUID] = None
    items: List[OrderItemResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: str  # CONFIRMED, PROCESSING, SHIPPED, DELIVERED, CANCELLED
