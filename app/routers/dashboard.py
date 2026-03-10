from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timedelta
from sqlalchemy.sql import extract
from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user
from app.models.product import Product
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# =========================
# SUMMARY ENDPOINT
# =========================
@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):

    # Total products
    total_products = db.query(Product).filter(
        Product.user_id == current_user.id
    ).count()

    # Total stock value
    products = db.query(Product).filter(
        Product.user_id == current_user.id
    ).all()

    total_stock_value = sum(
        p.purchase_price * p.stock_quantity for p in products
    )

    # Total invoices
    total_invoices = db.query(Invoice).filter(
        Invoice.user_id == current_user.id
    ).count()

    # Revenue today (FIXED timezone-safe logic)
    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = start_of_day + timedelta(days=1)

    revenue_today = db.query(
        func.sum(Invoice.total_amount)
    ).filter(
        Invoice.user_id == current_user.id,
        Invoice.created_at >= start_of_day,
        Invoice.created_at < end_of_day
    ).scalar() or 0

    # Low stock count
    low_stock_products = db.query(Product).filter(
        Product.user_id == current_user.id,
        Product.stock_quantity < 5
    ).count()

    return {
        "total_products": total_products,
        "total_stock_value": total_stock_value,
        "total_invoices": total_invoices,
        "revenue_today": revenue_today,
        "low_stock_products": low_stock_products
    }


# =========================
# REVENUE ANALYTICS
# =========================
@router.get("/revenue")
def get_revenue_analytics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):

    today = date.today()

    # Total revenue (all time)
    total_revenue_all_time = db.query(
        func.sum(Invoice.total_amount)
    ).filter(
        Invoice.user_id == current_user.id
    ).scalar() or 0

    # Revenue this month
    revenue_this_month = db.query(
        func.sum(Invoice.total_amount)
    ).filter(
        Invoice.user_id == current_user.id,
        extract("month", Invoice.created_at) == today.month,
        extract("year", Invoice.created_at) == today.year
    ).scalar() or 0

    # Revenue today (FIXED)
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = start_of_day + timedelta(days=1)

    revenue_today = db.query(
        func.sum(Invoice.total_amount)
    ).filter(
        Invoice.user_id == current_user.id,
        Invoice.created_at >= start_of_day,
        Invoice.created_at < end_of_day
    ).scalar() or 0

    # Monthly breakdown
    monthly_data = db.query(
        extract("year", Invoice.created_at).label("year"),
        extract("month", Invoice.created_at).label("month"),
        func.sum(Invoice.total_amount).label("revenue")
    ).filter(
        Invoice.user_id == current_user.id
    ).group_by("year", "month").order_by("year", "month").all()

    monthly_breakdown = [
        {
            "month": f"{int(row.year)}-{int(row.month):02}",
            "revenue": float(row.revenue)
        }
        for row in monthly_data
    ]

    return {
        "total_revenue_all_time": total_revenue_all_time,
        "revenue_this_month": revenue_this_month,
        "revenue_today": revenue_today,
        "monthly_breakdown": monthly_breakdown
    }

@router.get("/insights")
def get_dashboard_insights(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):

    # -----------------------------
    # Top Selling Products
    # -----------------------------
    top_selling = db.query(
        Product.product_name,
        func.sum(InvoiceItem.quantity).label("units_sold")
    ).join(
        InvoiceItem, Product.id == InvoiceItem.product_id
    ).join(
        Invoice, Invoice.id == InvoiceItem.invoice_id
    ).filter(
        Product.user_id == current_user.id
    ).group_by(
        Product.product_name
    ).order_by(
        func.sum(InvoiceItem.quantity).desc()
    ).limit(5).all()

    top_selling_products = [
        {
            "product_name": row.product_name,
            "units_sold": int(row.units_sold)
        }
        for row in top_selling
    ]

    # -----------------------------
    # Low Stock Products
    # -----------------------------
    low_stock = db.query(Product).filter(
        Product.user_id == current_user.id,
        Product.stock_quantity < 5
    ).all()

    low_stock_products = [
        {
            "product_name": p.product_name,
            "stock_quantity": p.stock_quantity
        }
        for p in low_stock
    ]

    return {
        "top_selling_products": top_selling_products,
        "low_stock_products": low_stock_products
    }