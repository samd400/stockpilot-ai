"""
Dashboard aggregation endpoint — queries billing DB for key business metrics.
"""
import os
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.core.database import get_db
from app.core.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _safe_query(func_call, default=0):
    try:
        result = func_call()
        return result if result is not None else default
    except Exception as e:
        logger.warning(f"Dashboard query failed: {e}")
        return default


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db), user: Dict = Depends(get_current_user)):
    """
    Returns key business metrics for the dashboard.
    Queries billing DB (invoices, invoice_items) for financial data.
    Product count fetched from inventory-service via internal call.
    """
    tenant_id = user["tenant_id"]

    # Import billing models (ai-service shares billing DB)
    try:
        from app.models.billing_models import Invoice, InvoiceItem
    except ImportError:
        # Fallback: import directly
        try:
            from sqlalchemy import text
            Invoice = None
            InvoiceItem = None
        except Exception:
            pass

    # Try to get invoice metrics using raw SQL for robustness
    try:
        from sqlalchemy import text

        # Total invoices
        total_invoices = db.execute(
            text("SELECT COUNT(*) FROM invoices WHERE tenant_id = :tid"),
            {"tid": tenant_id}
        ).scalar() or 0

        # Revenue today
        today = date.today().isoformat()
        revenue_today = db.execute(
            text("""SELECT COALESCE(SUM(total_amount), 0) FROM invoices
                    WHERE tenant_id = :tid AND status = 'paid'
                    AND DATE(created_at) = :today"""),
            {"tid": tenant_id, "today": today}
        ).scalar() or 0

        # Revenue this month
        first_of_month = date.today().replace(day=1).isoformat()
        revenue_month = db.execute(
            text("""SELECT COALESCE(SUM(total_amount), 0) FROM invoices
                    WHERE tenant_id = :tid AND status = 'paid'
                    AND created_at >= :start"""),
            {"tid": tenant_id, "start": first_of_month}
        ).scalar() or 0

        # Total customers from CRM (estimate from invoices)
        total_customers = db.execute(
            text("SELECT COUNT(DISTINCT customer_id) FROM invoices WHERE tenant_id = :tid AND customer_id IS NOT NULL"),
            {"tid": tenant_id}
        ).scalar() or 0

        # Total expenses this month
        total_expenses = db.execute(
            text("""SELECT COALESCE(SUM(amount), 0) FROM expenses
                    WHERE tenant_id = :tid AND date >= :start"""),
            {"tid": tenant_id, "start": first_of_month}
        ).scalar() or 0

    except Exception as e:
        logger.warning(f"DB query error in dashboard summary: {e}")
        total_invoices = 0
        revenue_today = 0
        revenue_month = 0
        total_customers = 0
        total_expenses = 0

    # Get product count from inventory-service via HTTP
    total_products = 0
    total_stock_value = 0
    low_stock_count = 0
    try:
        import httpx
        inventory_url = os.getenv("INVENTORY_SERVICE_URL", "http://inventory-service:8002")
        service_token = os.getenv("SERVICE_TOKEN", "")
        resp = httpx.get(
            f"{inventory_url}/products",
            params={"tenant_id": tenant_id, "limit": 1000},
            headers={"X-Service-Token": service_token},
            timeout=5.0
        )
        if resp.status_code == 200:
            data = resp.json()
            products = data.get("products", data) if isinstance(data, dict) else data
            if isinstance(products, list):
                total_products = len(products)
                for p in products:
                    stock = p.get("stock_quantity", 0) or 0
                    price = p.get("purchase_price", 0) or 0
                    total_stock_value += stock * price
                    if stock <= p.get("reorder_level", 10):
                        low_stock_count += 1
    except Exception as e:
        logger.warning(f"Could not reach inventory-service for product count: {e}")

    return {
        "total_products": total_products,
        "total_stock_value": round(total_stock_value, 2),
        "low_stock_count": low_stock_count,
        "total_invoices": int(total_invoices),
        "revenue_today": round(float(revenue_today), 2),
        "revenue_month": round(float(revenue_month), 2),
        "total_customers": int(total_customers),
        "total_expenses_month": round(float(total_expenses), 2),
    }


@router.get("/revenue")
def dashboard_revenue(months: int = 6, db: Session = Depends(get_db),
                       user: Dict = Depends(get_current_user)):
    """Monthly revenue breakdown for the chart."""
    tenant_id = user["tenant_id"]
    monthly_breakdown = []

    try:
        from sqlalchemy import text
        for i in range(months - 1, -1, -1):
            # Calculate month start/end
            target = datetime.now().replace(day=1) - timedelta(days=i * 28)
            month_start = target.replace(day=1, hour=0, minute=0, second=0)
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1)

            result = db.execute(
                text("""SELECT COALESCE(SUM(total_amount), 0) as revenue,
                               COUNT(*) as count
                        FROM invoices
                        WHERE tenant_id = :tid
                        AND status IN ('paid', 'PAID')
                        AND created_at >= :start AND created_at < :end"""),
                {"tid": tenant_id, "start": month_start, "end": month_end}
            ).fetchone()

            monthly_breakdown.append({
                "month": month_start.strftime("%b %Y"),
                "revenue": round(float(result[0] or 0), 2),
                "invoice_count": int(result[1] or 0),
            })
    except Exception as e:
        logger.warning(f"Revenue chart query failed: {e}")
        # Return empty placeholder data
        for i in range(months - 1, -1, -1):
            target = datetime.now().replace(day=1) - timedelta(days=i * 28)
            monthly_breakdown.append({
                "month": target.strftime("%b %Y"),
                "revenue": 0,
                "invoice_count": 0,
            })

    return {"monthly_breakdown": monthly_breakdown}


@router.get("/insights")
def dashboard_insights(db: Session = Depends(get_db), user: Dict = Depends(get_current_user)):
    """Top selling products and recent activity insights."""
    tenant_id = user["tenant_id"]
    top_selling = []
    recent_invoices = []

    try:
        from sqlalchemy import text

        # Top 5 selling products by quantity from invoice_items
        rows = db.execute(
            text("""SELECT product_name, product_id,
                           SUM(quantity) as total_qty,
                           SUM(line_total) as total_revenue
                    FROM invoice_items ii
                    JOIN invoices inv ON ii.invoice_id = inv.id
                    WHERE inv.tenant_id = :tid
                    AND inv.status IN ('paid', 'PAID')
                    GROUP BY product_name, product_id
                    ORDER BY total_qty DESC
                    LIMIT 5"""),
            {"tid": tenant_id}
        ).fetchall()

        for r in rows:
            top_selling.append({
                "product_name": r[0],
                "product_id": str(r[1]) if r[1] else None,
                "total_sold": int(r[2] or 0),
                "total_revenue": round(float(r[3] or 0), 2),
            })

        # Recent 5 invoices
        inv_rows = db.execute(
            text("""SELECT invoice_number, customer_name, total_amount, status, created_at
                    FROM invoices
                    WHERE tenant_id = :tid
                    ORDER BY created_at DESC
                    LIMIT 5"""),
            {"tid": tenant_id}
        ).fetchall()

        for r in inv_rows:
            recent_invoices.append({
                "invoice_number": r[0],
                "customer_name": r[1],
                "total_amount": round(float(r[2] or 0), 2),
                "status": r[3],
                "created_at": r[4].isoformat() if r[4] else None,
            })

    except Exception as e:
        logger.warning(f"Insights query failed: {e}")

    return {
        "top_selling_products": top_selling,
        "recent_invoices": recent_invoices,
    }
