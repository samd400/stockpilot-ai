"""Pricing Router — dynamic pricing recommendations & application."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from pydantic import BaseModel

from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user
from app.models.user import User
from app.models.pricing_rule import PricingRule
from app.services.pricing_agent import get_recommendations, apply_recommendation, analyze_and_recommend

router = APIRouter(prefix="/pricing", tags=["Pricing"])


class PricingRuleCreate(BaseModel):
    product_id: UUID
    region: Optional[str] = None
    margin_floor: float = 10.0
    dynamic_enabled: bool = True


class PricingRuleResponse(BaseModel):
    id: UUID
    product_id: UUID
    margin_floor: float
    dynamic_enabled: bool
    recommended_price: Optional[float] = None

    class Config:
        from_attributes = True


@router.post("/rules", response_model=PricingRuleResponse)
def create_pricing_rule(
    data: PricingRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create/update a pricing rule for a product."""
    import uuid as _uuid
    existing = db.query(PricingRule).filter(
        PricingRule.product_id == data.product_id, PricingRule.tenant_id == current_user.tenant_id
    ).first()
    if existing:
        existing.margin_floor = data.margin_floor
        existing.dynamic_enabled = data.dynamic_enabled
        existing.region = data.region
        db.commit()
        db.refresh(existing)
        return existing

    rule = PricingRule(
        id=_uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        product_id=data.product_id,
        region=data.region,
        margin_floor=data.margin_floor,
        dynamic_enabled=data.dynamic_enabled,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/recommendations")
def pricing_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get dynamic pricing recommendations for all enabled products."""
    return get_recommendations(db, str(current_user.tenant_id))


@router.get("/recommendations/{product_id}")
def product_recommendation(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get pricing recommendation for a single product."""
    return analyze_and_recommend(db, str(current_user.tenant_id), str(product_id))


@router.post("/apply/{product_id}")
def apply_price(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Apply the recommended price to a product."""
    result = apply_recommendation(db, str(current_user.tenant_id), str(product_id), str(current_user.id))
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
