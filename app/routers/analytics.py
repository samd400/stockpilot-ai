from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user

from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.product import Product
from app.services.stock_prediction_service import generate_stock_predictions
from app.services.business_summary_service import generate_business_summary


router = APIRouter(prefix="/analytics", tags=["Analytics"])


# =====================================================
# STOCK PREDICTION (Already Built)
# =====================================================
@router.get("/stock-prediction")
def stock_prediction(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return generate_stock_predictions(db, current_user.id)


# =====================================================
# 30-DAY SALES TREND (NEW)
# =====================================================
@router.get("/sales-trend")
def get_sales_trend(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    results = db.query(
        func.date(Invoice.created_at).label("sale_date"),
        func.coalesce(func.sum(InvoiceItem.quantity), 0).label("total_quantity"),
        func.coalesce(func.sum(Invoice.total_amount), 0).label("total_revenue")
    ).join(
        InvoiceItem, Invoice.id == InvoiceItem.invoice_id
    ).filter(
        Invoice.user_id == current_user.id,
        Invoice.created_at >= thirty_days_ago
    ).group_by(
        func.date(Invoice.created_at)
    ).order_by(
        func.date(Invoice.created_at)
    ).all()

    response = []

    for row in results:
        response.append({
            "date": str(row.sale_date),
            "total_quantity": int(row.total_quantity),
            "total_revenue": float(row.total_revenue)
        })

    return response

@router.get("/business-summary")
def business_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return generate_business_summary(db, current_user.id)


# =====================================================
# TOP SELLING PRODUCTS (NEW)
# =====================================================
@router.get("/top-products")
def get_top_products(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    # Base query
    base_query = db.query(
        InvoiceItem.product_id,
        func.sum(InvoiceItem.quantity).label("total_quantity_sold"),
        func.sum(InvoiceItem.quantity * Product.selling_price).label("total_revenue")
    ).join(
        Invoice, Invoice.id == InvoiceItem.invoice_id
    ).join(
        Product, Product.id == InvoiceItem.product_id
    ).filter(
        Invoice.user_id == current_user.id,
        Invoice.created_at >= thirty_days_ago
    ).group_by(
        InvoiceItem.product_id
    )

    # Top 5 by revenue
    top_by_revenue = base_query.order_by(
        func.sum(InvoiceItem.quantity * Product.selling_price).desc()
    ).limit(5).all()

    # Top 5 by quantity
    top_by_quantity = base_query.order_by(
        func.sum(InvoiceItem.quantity).desc()
    ).limit(5).all()

    # Function to resolve product details
    def resolve_products(results):
        response = []
        for row in results:
            product = db.query(Product).filter(Product.id == row.product_id).first()
            if product:
                response.append({
                    "product_name": product.product_name,
                    "total_quantity_sold": int(row.total_quantity_sold),
                    "total_revenue": float(row.total_revenue)
                })
        return response

    return {
        "top_by_revenue": resolve_products(top_by_revenue),
        "top_by_quantity": resolve_products(top_by_quantity)
    }


# =====================================================
# PROFIT-LOSS TREND (NEW)
# =====================================================
@router.get("/profit-loss-trend")
def get_profit_loss_trend(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    results = db.query(
        func.date(Invoice.created_at).label("date"),
        func.sum(InvoiceItem.quantity * Product.selling_price).label("total_revenue"),
        func.sum(InvoiceItem.quantity * Product.purchase_price).label("total_cogs"),
        (
            func.sum(InvoiceItem.quantity * Product.selling_price) - 
            func.sum(InvoiceItem.quantity * Product.purchase_price)
        ).label("total_profit")
    ).join(
        InvoiceItem, Invoice.id == InvoiceItem.invoice_id
    ).join(
        Product, Product.id == InvoiceItem.product_id
    ).filter(
        Invoice.user_id == current_user.id,
        Invoice.created_at >= thirty_days_ago
    ).group_by(
        func.date(Invoice.created_at)
    ).order_by(
        func.date(Invoice.created_at)
    ).all()

    response = []
    for row in results:
        response.append({
            "date": str(row.date),
            "total_revenue": float(row.total_revenue),
            "total_cogs": float(row.total_cogs),
            "total_profit": float(row.total_profit)
        })

    return response


# =====================================================
# DEMAND FORECASTING
# =====================================================
@router.get("/forecast/{product_id}")
def get_demand_forecast(
    product_id: str,
    horizon_days: int = 30,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get demand forecast for a product using ML linear regression."""
    from app.ml.forecast import predict_demand
    result = predict_demand(
        db=db,
        tenant_id=str(current_user.tenant_id),
        product_id=product_id,
        horizon_days=horizon_days,
    )
    return result


