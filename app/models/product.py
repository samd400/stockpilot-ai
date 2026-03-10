from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Core fields
    product_name = Column(String, nullable=False)
    sku = Column(String, nullable=True, index=True)
    product_type = Column(String, default="physical")  # physical, service, bundle, digital, rental
    brand = Column(String, nullable=True)
    category = Column(String, nullable=True)

    # Pricing
    purchase_price = Column(Float, nullable=False, default=0)
    selling_price = Column(Float, nullable=False, default=0)
    currency = Column(String(3), default="INR")

    # Stock
    stock_quantity = Column(Integer, default=0)
    unit = Column(String, default="pcs")  # pcs, kg, ltr, box, etc.

    # Product attributes
    serialized = Column(Boolean, default=False)
    tax_exempt = Column(Boolean, default=False)
    variant_group_id = Column(UUID(as_uuid=True), nullable=True)
    warranty_months = Column(Integer, default=0)

    # Tax (legacy, prefer tax_engine)
    gst_percentage = Column(Float, default=18.0)
    hsn_code = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User")
