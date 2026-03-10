"""Dynamic Pricing Agent — analyzes demand, stock, and sets optimal prices."""

import uuid
import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.pricing_rule import PricingRule
from app.models.forecast import Forecast
from app.models.tenant import Tenant
from app.services.procurement_service import log_agent_audit

logger = logging.getLogger(__name__)

AGENT_NAME = "pricing_agent"


def analyze_and_recommend(db: Session, tenant_id: str, product_id: str) -> Dict:
    """Analyze demand forecast and stock levels, return pricing recommendation."""
    product = db.query(Product).filter(Product.id == product_id, Product.tenant_id == tenant_id).first()
    if not product:
        return {"error": "Product not found"}

    # Get latest forecast
    forecast = db.query(Forecast).filter(
        Forecast.product_id == product_id, Forecast.tenant_id == tenant_id
    ).order_by(Forecast.created_at.desc()).first()

    # Get pricing rule
    rule = db.query(PricingRule).filter(
        PricingRule.product_id == product_id, PricingRule.tenant_id == tenant_id
    ).first()

    base_price = product.selling_price
    multiplier = 1.0
    reasons = []

    # Stock-based adjustment
    if product.stock_quantity <= 5:
        multiplier += 0.10  # Low stock → price up 10%
        reasons.append("Low stock (+10%)")
    elif product.stock_quantity > 100:
        multiplier -= 0.05  # Overstock → price down 5%
        reasons.append("Overstock (-5%)")

    # Demand-based adjustment
    if forecast and forecast.predicted_quantity:
        daily_demand = forecast.predicted_quantity / max(forecast.horizon_days, 1)
        if daily_demand > 5:
            multiplier += 0.08  # High demand → price up 8%
            reasons.append(f"High demand ({daily_demand:.1f}/day, +8%)")
        elif daily_demand < 1:
            multiplier -= 0.05
            reasons.append(f"Low demand ({daily_demand:.1f}/day, -5%)")

    recommended_price = round(base_price * multiplier, 2)

    # Respect margin floor
    margin_floor = rule.margin_floor if rule else 10.0
    purchase_price = getattr(product, 'purchase_price', None) or (base_price * 0.6)
    min_price = purchase_price * (1 + margin_floor / 100)
    if recommended_price < min_price:
        recommended_price = round(min_price, 2)
        reasons.append(f"Floor enforced (min margin {margin_floor}%)")

    return {
        "product_id": str(product_id),
        "product_name": product.product_name,
        "current_price": base_price,
        "recommended_price": recommended_price,
        "multiplier": round(multiplier, 3),
        "reasons": reasons,
        "margin_floor": margin_floor,
        "stock_quantity": product.stock_quantity,
    }


def get_recommendations(db: Session, tenant_id: str) -> List[Dict]:
    """Get pricing recommendations for all products with dynamic pricing enabled."""
    rules = db.query(PricingRule).filter(
        PricingRule.tenant_id == tenant_id, PricingRule.dynamic_enabled == True
    ).all()

    results = []
    for rule in rules:
        rec = analyze_and_recommend(db, tenant_id, str(rule.product_id))
        if "error" not in rec:
            results.append(rec)
    return results


def apply_recommendation(db: Session, tenant_id: str, product_id: str, user_id: str = None) -> Dict:
    """Apply the pricing recommendation to the product."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if tenant and not tenant.allow_dynamic_pricing:
        return {"error": "Dynamic pricing is disabled for this tenant"}

    rec = analyze_and_recommend(db, tenant_id, product_id)
    if "error" in rec:
        return rec

    product = db.query(Product).filter(Product.id == product_id, Product.tenant_id == tenant_id).first()
    old_price = product.selling_price
    product.selling_price = rec["recommended_price"]

    # Update pricing rule with recommendation
    rule = db.query(PricingRule).filter(
        PricingRule.product_id == product_id, PricingRule.tenant_id == tenant_id
    ).first()
    if rule:
        rule.recommended_price = rec["recommended_price"]
        rule.recommendation_reason = "; ".join(rec["reasons"])

    db.commit()

    log_agent_audit(db, tenant_id, AGENT_NAME, "price_applied",
                    input_data={"product_id": product_id, "old_price": old_price},
                    output_data={"new_price": rec["recommended_price"], "reasons": rec["reasons"]},
                    status="success")

    return {**rec, "applied": True, "old_price": old_price}
