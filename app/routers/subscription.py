from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user
from app.models.user import User
from app.models.user_subscription import UserSubscription, SubscriptionStatus
from app.models.subscription_plan import SubscriptionPlan
from app.schemas.user_subscription import UserSubscriptionCreate, UserSubscriptionResponse
from typing import List

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.post("/", response_model=UserSubscriptionResponse)
def create_subscription(
    subscription: UserSubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new subscription for the user"""
    
    # Check if plan exists
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == subscription.subscription_plan_id
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    
    # Check if user already has active subscription
    existing = db.query(UserSubscription).filter(
        UserSubscription.user_id == current_user.id,
        UserSubscription.status == SubscriptionStatus.ACTIVE
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User already has an active subscription")
    
    # Create subscription
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=30)  # 30-day trial or monthly
    renewal_date = end_date
    
    new_subscription = UserSubscription(
        user_id=current_user.id,
        subscription_plan_id=subscription.subscription_plan_id,
        status=SubscriptionStatus.ACTIVE,
        start_date=start_date,
        end_date=end_date,
        renewal_date=renewal_date,
        payment_method=subscription.payment_method,
        amount_paid=plan.price
    )
    
    db.add(new_subscription)
    
    # Update user subscription
    current_user.subscription_plan_id = subscription.subscription_plan_id
    current_user.subscription_expiry = end_date
    
    db.commit()
    db.refresh(new_subscription)
    return new_subscription


@router.get("/", response_model=List[UserSubscriptionResponse])
def list_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all subscriptions for the current user"""
    subscriptions = db.query(UserSubscription).filter(
        UserSubscription.user_id == current_user.id
    ).all()
    return subscriptions


@router.get("/active", response_model=UserSubscriptionResponse)
def get_active_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the active subscription for the current user"""
    subscription = db.query(UserSubscription).filter(
        UserSubscription.user_id == current_user.id,
        UserSubscription.status == SubscriptionStatus.ACTIVE
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    return subscription


@router.post("/{subscription_id}/cancel")
def cancel_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a subscription"""
    subscription = db.query(UserSubscription).filter(
        UserSubscription.id == subscription_id,
        UserSubscription.user_id == current_user.id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    subscription.status = SubscriptionStatus.CANCELLED
    db.commit()
    
    return {"message": "Subscription cancelled successfully"}


@router.post("/{subscription_id}/upgrade")
def upgrade_subscription(
    subscription_id: str,
    new_plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upgrade to a different subscription plan"""
    subscription = db.query(UserSubscription).filter(
        UserSubscription.id == subscription_id,
        UserSubscription.user_id == current_user.id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Check if new plan exists
    new_plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == new_plan_id
    ).first()
    
    if not new_plan:
        raise HTTPException(status_code=404, detail="New subscription plan not found")
    
    # Update subscription
    subscription.subscription_plan_id = new_plan_id
    subscription.amount_paid = new_plan.price
    
    # Update user
    current_user.subscription_plan_id = new_plan_id
    
    db.commit()
    db.refresh(subscription)
    
    return {"message": "Subscription upgraded successfully", "subscription": subscription}
