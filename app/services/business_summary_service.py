from sqlalchemy.orm import Session
from app.services.stock_prediction_service import generate_stock_predictions


def generate_business_summary(db: Session, user_id):

    predictions = generate_stock_predictions(db, user_id)

    total_capital_blocked = 0
    total_revenue_loss = 0
    total_profit_loss = 0

    high_risk_count = 0
    dead_stock_count = 0
    fast_moving_count = 0

    for item in predictions:

        total_capital_blocked += item["capital_blocked"]
        total_revenue_loss += item["estimated_revenue_loss_30_days"]
        total_profit_loss += item["estimated_profit_loss_30_days"]

        if item["risk_level"] in ["Critical", "High"]:
            high_risk_count += 1

        if item["movement_type"] == "Dead Stock":
            dead_stock_count += 1

        if item["movement_type"] == "Fast Moving":
            fast_moving_count += 1

    total_products = len(predictions)

    # Inventory health score (simple formula)
    if total_products > 0:
        health_score = round(
            (fast_moving_count / total_products) * 100,
            1
        )
    else:
        health_score = 0

    return {
        "total_products": total_products,
        "total_capital_blocked": round(total_capital_blocked, 2),
        "total_projected_revenue_loss_30_days": round(total_revenue_loss, 2),
        "total_projected_profit_loss_30_days": round(total_profit_loss, 2),
        "high_risk_products": high_risk_count,
        "dead_stock_products": dead_stock_count,
        "fast_moving_products": fast_moving_count,
        "inventory_health_score_percent": health_score
    }
