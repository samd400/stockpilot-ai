from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

# =====================================================
# Supplier Schemas
# =====================================================
class SupplierBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None

class SupplierCreate(SupplierBase):
    pass

class Supplier(SupplierBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# =====================================================
# Purchase Order Item Schemas
# =====================================================
class PurchaseOrderItemBase(BaseModel):
    product_id: str
    quantity: int
    purchase_price: float

class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    pass

class PurchaseOrderItem(PurchaseOrderItemBase):
    id: str
    purchase_order_id: str
    total_price: float

    class Config:
        orm_mode = True

# =====================================================
# Purchase Order Schemas
# =====================================================
class PurchaseOrderBase(BaseModel):
    supplier_id: str
    expected_delivery_date: Optional[datetime] = None
    status: Optional[str] = "PENDING"

class PurchaseOrderCreate(PurchaseOrderBase):
    items: List[PurchaseOrderItemCreate]

class PurchaseOrder(PurchaseOrderBase):
    id: str
    user_id: str
    order_date: datetime
    total_amount: float
    items: List[PurchaseOrderItem] = []
    supplier: Supplier

    class Config:
        orm_mode = True

class PurchaseOrderStatusUpdate(BaseModel):
    status: str # PENDING, COMPLETED, CANCELLED
