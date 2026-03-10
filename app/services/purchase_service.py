from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User
from app.schemas.purchase import PurchaseOrderCreate, PurchaseOrderStatusUpdate, SupplierCreate
from app.models.supplier import Supplier as SupplierModel
from app.models.purchase_order import PurchaseOrder as PurchaseOrderModel
from app.models.purchase_order import PurchaseOrderItem as PurchaseOrderItemModel
from app.models.product import Product as ProductModel
import uuid

def create_supplier(db: Session, current_user: User, supplier: SupplierCreate):
    new_supplier = SupplierModel(
        **supplier.dict(),
        id=str(uuid.uuid4()),
        user_id=current_user.id
    )
    db.add(new_supplier)
    db.commit()
    db.refresh(new_supplier)
    return new_supplier

def get_suppliers(db: Session, current_user: User):
    return db.query(SupplierModel).filter(SupplierModel.user_id == current_user.id).all()

def get_purchase_orders(db: Session, current_user: User):
    return db.query(PurchaseOrderModel).filter(PurchaseOrderModel.user_id == current_user.id).all()

def get_purchase_order(db: Session, current_user: User, order_id: str):
    order = db.query(PurchaseOrderModel).filter(
        PurchaseOrderModel.id == order_id,
        PurchaseOrderModel.user_id == current_user.id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return order

def create_purchase_order(db: Session, current_user: User, order: PurchaseOrderCreate):
    # Verify supplier exists
    supplier = db.query(SupplierModel).filter(
        SupplierModel.id == order.supplier_id,
        SupplierModel.user_id == current_user.id
    ).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    new_order = PurchaseOrderModel(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        supplier_id=order.supplier_id,
        expected_delivery_date=order.expected_delivery_date,
        status=order.status,
        total_amount=0  # Will be calculated below
    )

    total_amount = 0
    for item_data in order.items:
        # Verify product exists
        product = db.query(ProductModel).filter(
            ProductModel.id == item_data.product_id,
            ProductModel.user_id == current_user.id
        ).first()
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product with id {item_data.product_id} not found"
            )

        total_price = item_data.quantity * item_data.purchase_price
        total_amount += total_price

        new_item = PurchaseOrderItemModel(
            id=str(uuid.uuid4()),
            purchase_order_id=new_order.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            purchase_price=item_data.purchase_price,
            total_price=total_price
        )
        db.add(new_item)

    new_order.total_amount = total_amount
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

def update_purchase_order_status(db: Session, current_user: User, order_id: str, status_update: PurchaseOrderStatusUpdate):
    order = db.query(PurchaseOrderModel).filter(
        PurchaseOrderModel.id == order_id,
        PurchaseOrderModel.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    if order.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="Completed order cannot be modified")

    order.status = status_update.status

    if status_update.status == "COMPLETED":
        for item in order.items:
            product = db.query(ProductModel).filter(
                ProductModel.id == item.product_id,
                ProductModel.user_id == current_user.id
            ).first()
            if product:
                product.stock_quantity += item.quantity

    db.commit()
    db.refresh(order)
    return order
