from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user, get_current_tenant_id
from app.models.user import User
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductResponse
import uuid
from app.services.plan_guard import check_product_limit
router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(check_product_limit)
):

    new_product = Product(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        product_name=product.product_name,
        sku=product.sku,
        product_type=product.product_type,
        brand=product.brand,
        category=product.category,
        purchase_price=product.purchase_price,
        selling_price=product.selling_price,
        currency=product.currency,
        stock_quantity=product.stock_quantity,
        unit=product.unit,
        serialized=product.serialized,
        tax_exempt=product.tax_exempt,
        variant_group_id=product.variant_group_id,
        warranty_months=product.warranty_months,
        gst_percentage=product.gst_percentage,
        hsn_code=product.hsn_code
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


@router.get("/", response_model=list[ProductResponse])
def list_products(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return db.query(Product).filter(Product.tenant_id == current_user.tenant_id).all()
