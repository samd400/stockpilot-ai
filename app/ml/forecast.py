"""ML Demand Forecasting — lightweight linear regression-based demand prediction."""

import logging
import uuid
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.invoice_item import InvoiceItem
from app.models.invoice import Invoice
from app.models.product import Product
from app.models.forecast import Forecast

logger = logging.getLogger(__name__)


def _get_daily_sales(db: Session, product_id: str, days: int = 90) -> List[float]:
    """Get daily sales quantities for the past N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    results = db.query(
        func.date(Invoice.created_at).label("day"),
        func.coalesce(func.sum(InvoiceItem.quantity), 0).label("qty"),
    ).join(
        Invoice, Invoice.id == InvoiceItem.invoice_id
    ).filter(
        InvoiceItem.product_id == product_id,
        Invoice.created_at >= cutoff,
    ).group_by(func.date(Invoice.created_at)).order_by(func.date(Invoice.created_at)).all()

    # Fill gaps with zeros
    daily = {}
    for row in results:
        daily[str(row.day)] = float(row.qty)

    sales = []
    for i in range(days):
        d = (cutoff + timedelta(days=i)).strftime("%Y-%m-%d")
        sales.append(daily.get(d, 0.0))

    return sales


def train_forecast_model(daily_sales: List[float]) -> Dict:
    """Train a simple linear regression on daily sales data."""
    n = len(daily_sales)
    if n < 7:
        avg = sum(daily_sales) / max(n, 1)
        return {"slope": 0, "intercept": avg, "model": "fallback_average"}

    # Simple linear regression: y = slope * x + intercept
    x_mean = (n - 1) / 2.0
    y_mean = sum(daily_sales) / n

    numerator = sum((i - x_mean) * (daily_sales[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))

    slope = numerator / denominator if denominator != 0 else 0
    intercept = y_mean - slope * x_mean

    # R² for confidence
    ss_res = sum((daily_sales[i] - (slope * i + intercept)) ** 2 for i in range(n))
    ss_tot = sum((daily_sales[i] - y_mean) ** 2 for i in range(n))
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    return {"slope": slope, "intercept": intercept, "r_squared": max(r_squared, 0), "model": "linear_regression"}


def predict_demand(
    db: Session,
    tenant_id: str,
    product_id: str,
    horizon_days: int = 30,
    history_days: int = 90,
) -> Dict:
    """Predict demand for a product over the given horizon."""
    product = db.query(Product).filter(Product.id == product_id, Product.tenant_id == tenant_id).first()
    if not product:
        return {"error": "Product not found"}

    daily_sales = _get_daily_sales(db, product_id, history_days)
    model = train_forecast_model(daily_sales)

    # Predict future: start from end of training data
    n = len(daily_sales)
    future_predictions = [max(model["slope"] * (n + d) + model["intercept"], 0) for d in range(horizon_days)]
    total_predicted = sum(future_predictions)

    # Confidence interval (±20% for simple model, tighter with higher R²)
    r2 = model.get("r_squared", 0)
    margin = 0.4 * (1 - r2)  # Better fit → narrower interval
    confidence_low = total_predicted * (1 - margin)
    confidence_high = total_predicted * (1 + margin)

    # Store prediction
    forecast = Forecast(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        product_id=product_id,
        horizon_days=horizon_days,
        predicted_quantity=round(total_predicted, 2),
        confidence_low=round(max(confidence_low, 0), 2),
        confidence_high=round(confidence_high, 2),
        model_type=model["model"],
    )
    db.add(forecast)
    db.commit()

    return {
        "product_id": str(product_id),
        "product_name": product.product_name,
        "horizon_days": horizon_days,
        "predicted_quantity": round(total_predicted, 2),
        "confidence_low": round(max(confidence_low, 0), 2),
        "confidence_high": round(confidence_high, 2),
        "model_type": model["model"],
        "daily_forecast": [round(p, 2) for p in future_predictions],
        "current_stock": product.stock_quantity,
        "stock_covers_days": round(product.stock_quantity / (total_predicted / horizon_days), 1) if total_predicted > 0 else 999,
    }
