import uuid
import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.core.deps import get_current_user, require_inventory_role, require_any_role
from app.models.product import Product

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/")
def list_products(search: Optional[str] = None, category: Optional[str] = None,
                   brand: Optional[str] = None, low_stock: bool = False,
                   skip: int = 0, limit: int = 50,
                   db: Session = Depends(get_db), user: Dict = Depends(require_any_role)):
    q = db.query(Product).filter(Product.tenant_id == user["tenant_id"],
                                  Product.is_active == True)
    if search:
        q = q.filter(or_(Product.product_name.ilike(f"%{search}%"),
                          Product.sku.ilike(f"%{search}%"),
                          Product.barcode.ilike(f"%{search}%")))
    if category:
        q = q.filter(Product.category == category)
    if brand:
        q = q.filter(Product.brand == brand)
    if low_stock:
        q = q.filter(Product.stock_quantity <= Product.reorder_level)
    products = q.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()
    return [_product_dict(p) for p in products]


@router.post("/", status_code=201)
def create_product(payload: Dict[str, Any], db: Session = Depends(get_db),
                   user: Dict = Depends(require_inventory_role)):
    if payload.get("sku"):
        existing = db.query(Product).filter(Product.sku == payload["sku"],
                                             Product.tenant_id == user["tenant_id"]).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"SKU '{payload['sku']}' already exists")
    product = Product(
        id=uuid.uuid4(), tenant_id=user["tenant_id"], user_id=user["user_id"],
        **{k: v for k, v in payload.items() if hasattr(Product, k) and k not in ("id", "tenant_id", "user_id")}
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return _product_dict(product)


@router.get("/{product_id}")
def get_product(product_id: str, db: Session = Depends(get_db),
                user: Dict = Depends(require_any_role)):
    product = db.query(Product).filter(Product.id == product_id,
                                        Product.tenant_id == user["tenant_id"]).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return _product_dict(product)


@router.patch("/{product_id}")
def update_product(product_id: str, payload: Dict[str, Any], db: Session = Depends(get_db),
                   user: Dict = Depends(require_inventory_role)):
    product = db.query(Product).filter(Product.id == product_id,
                                        Product.tenant_id == user["tenant_id"]).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    protected = {"id", "tenant_id", "user_id", "created_at"}
    for k, v in payload.items():
        if k not in protected and hasattr(product, k):
            setattr(product, k, v)
    db.commit()
    db.refresh(product)
    return _product_dict(product)


@router.delete("/{product_id}", status_code=200)
def delete_product(product_id: str, db: Session = Depends(get_db),
                   user: Dict = Depends(require_inventory_role)):
    product = db.query(Product).filter(Product.id == product_id,
                                        Product.tenant_id == user["tenant_id"]).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = False
    db.commit()
    return {"message": "Product deactivated"}


@router.get("/categories/list")
def list_categories(db: Session = Depends(get_db), user: Dict = Depends(require_any_role)):
    cats = db.query(Product.category).filter(
        Product.tenant_id == user["tenant_id"], Product.category.isnot(None),
        Product.is_active == True
    ).distinct().all()
    return [c[0] for c in cats if c[0]]


@router.get("/brands/list")
def list_brands(db: Session = Depends(get_db), user: Dict = Depends(require_any_role)):
    brands = db.query(Product.brand).filter(
        Product.tenant_id == user["tenant_id"], Product.brand.isnot(None),
        Product.is_active == True
    ).distinct().all()
    return [b[0] for b in brands if b[0]]


def _product_dict(p: Product) -> Dict:
    return {
        "id": str(p.id), "product_name": p.product_name, "sku": p.sku,
        "product_type": p.product_type, "brand": p.brand, "category": p.category,
        "purchase_price": p.purchase_price, "selling_price": p.selling_price,
        "currency": p.currency, "stock_quantity": p.stock_quantity, "unit": p.unit,
        "reorder_level": p.reorder_level, "gst_percentage": p.gst_percentage,
        "hsn_code": p.hsn_code, "tax_code": p.tax_code, "barcode": p.barcode,
        "warranty_months": p.warranty_months, "is_active": p.is_active,
        "created_at": p.created_at.isoformat(),
    }
