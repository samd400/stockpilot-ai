from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class ProductCreate(BaseModel):
    product_name: str
    sku: Optional[str] = None
    product_type: str = "physical"  # physical, service, bundle, digital, rental
    brand: Optional[str] = None
    category: Optional[str] = None
    purchase_price: float = 0
    selling_price: float = 0
    currency: str = "INR"
    stock_quantity: int = 0
    unit: str = "pcs"
    serialized: bool = False
    tax_exempt: bool = False
    variant_group_id: Optional[UUID] = None
    warranty_months: int = 0
    gst_percentage: Optional[float] = 18.0
    hsn_code: Optional[str] = None


class ProductResponse(BaseModel):
    id: UUID
    product_name: str
    sku: Optional[str] = None
    product_type: str = "physical"
    brand: Optional[str] = None
    category: Optional[str] = None
    purchase_price: float
    selling_price: float
    currency: str = "INR"
    stock_quantity: int
    unit: str = "pcs"
    serialized: bool = False
    tax_exempt: bool = False
    warranty_months: Optional[int] = None
    gst_percentage: Optional[float] = None
    hsn_code: Optional[str] = None

    class Config:
        from_attributes = True
