import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)

    product_name = Column(String, nullable=False)
    sku = Column(String, nullable=True, index=True)
    product_type = Column(String, default="physical")
    brand = Column(String, nullable=True)
    category = Column(String, nullable=True)
    sub_category = Column(String, nullable=True)
    description = Column(String, nullable=True)

    purchase_price = Column(Float, default=0)
    selling_price = Column(Float, default=0)
    currency = Column(String(3), default="INR")

    stock_quantity = Column(Integer, default=0)
    unit = Column(String, default="pcs")
    reorder_level = Column(Integer, default=10)
    max_stock_level = Column(Integer, nullable=True)

    serialized = Column(Boolean, default=False)
    tax_exempt = Column(Boolean, default=False)
    variant_group_id = Column(UUID(as_uuid=True), nullable=True)
    warranty_months = Column(Integer, default=0)

    gst_percentage = Column(Float, default=18.0)
    hsn_code = Column(String, nullable=True)
    tax_code = Column(String, nullable=True)

    barcode = Column(String, nullable=True, index=True)
    image_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
