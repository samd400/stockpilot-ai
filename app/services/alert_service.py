from sqlalchemy.orm import Session
from app.models.alert import Alert
from app.services.stock_prediction_service import generate_stock_predictions


def generate_smart_alerts(db: Session, user_id):

    predictions = generate_stock_predictions(db, user_id)

    created_count = 0

    for product in predictions:

        # 🔴 Critical Stock
        if product["risk_level"] == "Critical":
            alert = Alert(
                user_id=user_id,
                title="Critical Stock Alert",
                message=f"{product['product_name']} will run out very soon.",
                type="stock_alert"
            )
            db.add(alert)
            created_count += 1

        # 🧊 Dead Stock
        if product["movement_type"] == "Dead Stock":
            alert = Alert(
                user_id=user_id,
                title="Dead Stock Detected",
                message=f"{product['product_name']} is not selling.",
                type="stock_alert"
            )
            db.add(alert)
            created_count += 1

        # 💰 Profit Loss Risk
        if product["estimated_profit_loss_30_days"] > 0:
            alert = Alert(
                user_id=user_id,
                title="Potential Profit Loss",
                message=(
                    f"{product['product_name']} may cause "
                    f"₹{product['estimated_profit_loss_30_days']} profit loss."
                ),
                type="profit_alert"
            )
            db.add(alert)
            created_count += 1

    db.commit()

    return {"alerts_created": created_count}
