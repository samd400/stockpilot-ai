"""
Internal endpoints — called by other microservices only (no user auth, service token required).
"""
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import verify_service_token
from app.models.product import Product

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/internal", tags=["Internal"])


@router.post("/stock/deduct")
def deduct_stock(payload: Dict[str, Any], db: Session = Depends(get_db),
                 _: bool = Depends(verify_service_token)):
    """Deduct stock for invoice creation. Called by billing-service."""
    tenant_id = payload.get("tenant_id")
    items = payload.get("items", [])
    if not tenant_id or not items:
        raise HTTPException(status_code=400, detail="tenant_id and items required")

    # Validate all items first
    products = {}
    for item in items:
        product = db.query(Product).filter(
            Product.id == item["product_id"],
            Product.tenant_id == tenant_id,
            Product.is_active == True,
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item['product_id']} not found")
        if product.stock_quantity < item["quantity"]:
            raise HTTPException(status_code=409,
                                detail=f"Insufficient stock for {product.product_name}: "
                                       f"available={product.stock_quantity}, requested={item['quantity']}")
        products[item["product_id"]] = product

    # Deduct all
    deducted = []
    for item in items:
        product = products[item["product_id"]]
        product.stock_quantity -= item["quantity"]
        deducted.append({"product_id": item["product_id"], "quantity_deducted": item["quantity"],
                          "remaining": product.stock_quantity})
        logger.info(f"Deducted {item['quantity']} from product {product.product_name} "
                    f"(tenant {tenant_id})")
    db.commit()
    return {"success": True, "deducted": deducted}


@router.post("/stock/restore")
def restore_stock(payload: Dict[str, Any], db: Session = Depends(get_db),
                  _: bool = Depends(verify_service_token)):
    """Restore stock on invoice cancellation."""
    tenant_id = payload.get("tenant_id")
    items = payload.get("items", [])
    restored = []
    for item in items:
        product = db.query(Product).filter(Product.id == item["product_id"],
                                            Product.tenant_id == tenant_id).first()
        if product:
            product.stock_quantity += item["quantity"]
            restored.append({"product_id": item["product_id"], "restored": item["quantity"]})
    db.commit()
    return {"success": True, "restored": restored}


@router.get("/products/{product_id}")
def get_product_internal(product_id: str, tenant_id: str,
                          db: Session = Depends(get_db), _: bool = Depends(verify_service_token)):
    """Get product info for cross-service use."""
    product = db.query(Product).filter(Product.id == product_id,
                                        Product.tenant_id == tenant_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {
        "id": str(product.id), "product_name": product.product_name,
        "sku": product.sku, "selling_price": product.selling_price,
        "purchase_price": product.purchase_price, "stock_quantity": product.stock_quantity,
        "gst_percentage": product.gst_percentage, "hsn_code": product.hsn_code,
        "warranty_months": product.warranty_months, "currency": product.currency,
    }
