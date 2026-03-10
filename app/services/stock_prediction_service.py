from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.models.product import Product
from app.models.invoice_item import InvoiceItem
from app.models.invoice import Invoice


def generate_stock_predictions(db: Session, user_id):

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    products = db.query(Product).filter(
        Product.user_id == user_id
    ).all()

    results = []

    for product in products:

        # =====================================
        # SALES DATA (LAST 30 DAYS)
        # =====================================
        total_sold = db.query(
            func.coalesce(func.sum(InvoiceItem.quantity), 0)
        ).join(
            Invoice, Invoice.id == InvoiceItem.invoice_id
        ).filter(
            Invoice.user_id == user_id,
            InvoiceItem.product_id == product.id,
            Invoice.created_at >= thirty_days_ago
        ).scalar()

        average_daily_sales = total_sold / 30 if total_sold else 0

        # =====================================
        # STOCKOUT ESTIMATION
        # =====================================
        if average_daily_sales > 0:
            estimated_stockout_days = round(
                product.stock_quantity / average_daily_sales, 1
            )
        else:
            estimated_stockout_days = None

        # =====================================
        # REORDER LOGIC
        # =====================================
        lead_time_days = 7  # supplier lead time

        if average_daily_sales > 0:
            reorder_point = average_daily_sales * lead_time_days

            recommended_reorder_quantity = max(
                round((average_daily_sales * 30) - product.stock_quantity),
                0
            )
        else:
            reorder_point = 0
            recommended_reorder_quantity = 0

        # =====================================
        # MOVEMENT CLASSIFICATION
        # =====================================
        if average_daily_sales >= 1:
            movement_type = "Fast Moving"
        elif average_daily_sales >= 0.2:
            movement_type = "Moderate"
        elif average_daily_sales > 0:
            movement_type = "Slow Moving"
        else:
            movement_type = "Dead Stock"

        # =====================================
        # RISK LEVEL
        # =====================================
        if estimated_stockout_days and estimated_stockout_days <= lead_time_days:
            risk_level = "Critical"
        elif estimated_stockout_days and estimated_stockout_days <= 5:
            risk_level = "High"
        elif estimated_stockout_days and estimated_stockout_days <= 15:
            risk_level = "Medium"
        elif estimated_stockout_days:
            risk_level = "Low"
        else:
            risk_level = "No Sales"

        # =====================================
        # 💰 PROFIT IMPACT ANALYSIS
        # =====================================
        profit_per_unit = product.selling_price - product.purchase_price

        expected_30_day_demand = average_daily_sales * 30

        lost_units = max(
            expected_30_day_demand - product.stock_quantity,
            0
        )

        estimated_revenue_loss = round(
            lost_units * product.selling_price,
            2
        )

        estimated_profit_loss = round(
            lost_units * profit_per_unit,
            2
        )

        # =====================================
        # 💸 CAPITAL BLOCKED ANALYSIS
        # =====================================
        capital_blocked = product.stock_quantity * product.purchase_price

        if movement_type == "Slow Moving":
            stock_health = "Overstock Risk"
        elif movement_type == "Dead Stock":
            stock_health = "Dead Investment"
        else:
            stock_health = "Healthy"

        # =====================================
        # FINAL RESPONSE OBJECT
        # =====================================
        results.append({
            "product_name": product.product_name,
            "current_stock": product.stock_quantity,
            "total_sold_last_30_days": total_sold,
            "average_daily_sales": round(average_daily_sales, 2),
            "estimated_stockout_days": estimated_stockout_days,
            "recommended_reorder_quantity": recommended_reorder_quantity,
            "movement_type": movement_type,
            "risk_level": risk_level,
            "estimated_revenue_loss_30_days": estimated_revenue_loss,
            "estimated_profit_loss_30_days": estimated_profit_loss,
            "capital_blocked": round(capital_blocked, 2),
            "stock_health": stock_health
        })

    return results
