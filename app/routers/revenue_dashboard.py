from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user
from app.models.user_subscription import UserSubscription, SubscriptionStatus
from app.models.payment_transaction import PaymentTransaction
from app.models.invoice import Invoice

router = APIRouter(prefix="/admin/revenue", tags=["Admin Revenue Dashboard"])


@router.get("/metrics")
def get_revenue_metrics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get MRR, ARR, and other revenue metrics for admin dashboard"""
    
    # Calculate MRR (Monthly Recurring Revenue)
    active_subscriptions = db.query(UserSubscription).filter(
        UserSubscription.status == SubscriptionStatus.ACTIVE
    ).all()
    
    mrr = sum(
        db.query(func.sum(func.cast(sub.plan.price, func.Float)))
        .filter(UserSubscription.id == sub.id)
        .scalar() or 0
        for sub in active_subscriptions
    )
    
    # Calculate ARR (Annual Recurring Revenue)
    arr = mrr * 12
    
    # Calculate churn rate
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    churned = db.query(UserSubscription).filter(
        UserSubscription.status == SubscriptionStatus.CANCELLED,
        UserSubscription.updated_at >= thirty_days_ago
    ).count()
    
    churn_rate = (churned / len(active_subscriptions) * 100) if active_subscriptions else 0
    
    # Total revenue
    total_revenue = db.query(func.sum(PaymentTransaction.amount)).filter(
        PaymentTransaction.status == "SUCCESS"
    ).scalar() or 0
    
    # Active subscriptions count
    active_count = len(active_subscriptions)
    
    return {
        "mrr": mrr,
        "arr": arr,
        "churn_rate": churn_rate,
        "total_revenue": total_revenue,
        "active_subscriptions": active_count,
        "calculated_at": datetime.utcnow()
    }


@router.get("/monthly-breakdown")
def get_monthly_revenue_breakdown(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get monthly revenue breakdown for the last 12 months"""
    
    twelve_months_ago = datetime.utcnow() - timedelta(days=365)
    
    monthly_data = db.query(
        func.date_trunc('month', PaymentTransaction.created_at).label("month"),
        func.sum(PaymentTransaction.amount).label("revenue")
    ).filter(
        PaymentTransaction.status == "SUCCESS",
        PaymentTransaction.created_at >= twelve_months_ago
    ).group_by(
        func.date_trunc('month', PaymentTransaction.created_at)
    ).order_by(
        func.date_trunc('month', PaymentTransaction.created_at)
    ).all()
    
    return [
        {
            "month": str(row.month),
            "revenue": float(row.revenue)
        }
        for row in monthly_data
    ]


@router.get("/subscription-breakdown")
def get_subscription_breakdown(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get breakdown of subscriptions by plan"""
    
    from app.models.subscription_plan import SubscriptionPlan
    
    breakdown = db.query(
        SubscriptionPlan.name,
        func.count(UserSubscription.id).label("count"),
        func.sum(SubscriptionPlan.price).label("total_revenue")
    ).join(
        UserSubscription, UserSubscription.subscription_plan_id == SubscriptionPlan.id
    ).filter(
        UserSubscription.status == SubscriptionStatus.ACTIVE
    ).group_by(
        SubscriptionPlan.name
    ).all()
    
    return [
        {
            "plan_name": row.name,
            "subscription_count": int(row.count),
            "total_revenue": float(row.total_revenue)
        }
        for row in breakdown
    ]


@router.get("/customer-metrics")
def get_customer_metrics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get customer acquisition and retention metrics"""
    
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # New customers in last 30 days
    new_customers = db.query(UserSubscription).filter(
        UserSubscription.created_at >= thirty_days_ago
    ).count()
    
    # Total customers
    total_customers = db.query(UserSubscription).filter(
        UserSubscription.status == SubscriptionStatus.ACTIVE
    ).count()
    
    # Customer lifetime value (average)
    ltv_data = db.query(func.avg(Invoice.total_amount)).scalar() or 0
    
    return {
        "new_customers_30d": new_customers,
        "total_active_customers": total_customers,
        "avg_customer_ltv": float(ltv_data),
        "calculated_at": datetime.utcnow()
    }
