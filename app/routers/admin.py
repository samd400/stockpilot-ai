from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.subscription_plan import SubscriptionPlan

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/plans")
def create_plan(
    name: str,
    price: float,
    max_products: int,
    max_invoices_per_month: int,
    db: Session = Depends(get_db)
):
    existing = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.name == name
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Plan already exists")

    plan = SubscriptionPlan(
        name=name,
        price=price,
        max_products=max_products,
        max_invoices_per_month=max_invoices_per_month
    )

    db.add(plan)
    db.commit()
    db.refresh(plan)

    return plan


@router.get("/plans")
def list_plans(
    db: Session = Depends(get_db)
):
    return db.query(SubscriptionPlan).all()
