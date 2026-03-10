from celery import shared_task
from app.core.database import SessionLocal
from app.models.user_subscription import UserSubscription, SubscriptionStatus
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@shared_task
def check_subscription_expiry():
    """Check for expired subscriptions and auto-downgrade to free plan"""
    
    db = SessionLocal()
    
    try:
        # Find expired subscriptions
        expired_subscriptions = db.query(UserSubscription).filter(
            UserSubscription.status == SubscriptionStatus.ACTIVE,
            UserSubscription.end_date <= datetime.utcnow()
        ).all()
        
        # Get free plan
        free_plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.name == "Free"
        ).first()
        
        if not free_plan:
            logger.warning("Free plan not found for auto-downgrade")
            return
        
        for subscription in expired_subscriptions:
            # Update subscription status
            subscription.status = SubscriptionStatus.EXPIRED
            
            # Get user
            user = db.query(User).filter(User.id == subscription.user_id).first()
            
            if user:
                # Auto-downgrade to free plan
                user.subscription_plan_id = free_plan.id
                user.subscription_expiry = None
                
                logger.info(f"Auto-downgraded user {user.id} to free plan")
        
        db.commit()
        logger.info(f"Processed {len(expired_subscriptions)} expired subscriptions")
        
    except Exception as e:
        logger.error(f"Error checking subscription expiry: {str(e)}")
        db.rollback()
    finally:
        db.close()


@shared_task
def send_subscription_expiry_reminder():
    """Send reminder emails for subscriptions expiring in 7 days"""
    
    db = SessionLocal()
    
    try:
        from datetime import timedelta
        
        # Find subscriptions expiring in 7 days
        expiry_date = datetime.utcnow() + timedelta(days=7)
        
        expiring_subscriptions = db.query(UserSubscription).filter(
            UserSubscription.status == SubscriptionStatus.ACTIVE,
            UserSubscription.end_date <= expiry_date,
            UserSubscription.end_date > datetime.utcnow()
        ).all()
        
        for subscription in expiring_subscriptions:
            user = db.query(User).filter(User.id == subscription.user_id).first()
            
            if user and user.email:
                # Send email notification
                logger.info(f"Sending expiry reminder to {user.email}")
                # TODO: Implement email sending via Celery task
        
        logger.info(f"Sent {len(expiring_subscriptions)} expiry reminders")
        
    except Exception as e:
        logger.error(f"Error sending expiry reminders: {str(e)}")
    finally:
        db.close()


@shared_task
def calculate_revenue_metrics():
    """Calculate MRR, ARR, and other revenue metrics"""
    
    db = SessionLocal()
    
    try:
        from app.models.revenue_metrics import RevenueMetrics
        from sqlalchemy import func
        
        # Get active subscriptions
        active_subscriptions = db.query(UserSubscription).filter(
            UserSubscription.status == SubscriptionStatus.ACTIVE
        ).all()
        
        # Calculate MRR
        mrr = sum(
            db.query(func.cast(sub.plan.price, func.Float))
            .filter(UserSubscription.id == sub.id)
            .scalar() or 0
            for sub in active_subscriptions
        )
        
        # Calculate ARR
        arr = mrr * 12
        
        # Calculate churn rate
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        churned = db.query(UserSubscription).filter(
            UserSubscription.status == SubscriptionStatus.CANCELLED,
            UserSubscription.updated_at >= thirty_days_ago
        ).count()
        
        churn_rate = (churned / len(active_subscriptions) * 100) if active_subscriptions else 0
        
        # Save metrics
        metrics = RevenueMetrics(
            mrr=mrr,
            arr=arr,
            churn_rate=churn_rate,
            active_subscriptions=str(len(active_subscriptions)),
            period_start=datetime.utcnow() - timedelta(days=30),
            period_end=datetime.utcnow()
        )
        
        db.add(metrics)
        db.commit()
        
        logger.info(f"Calculated revenue metrics - MRR: {mrr}, ARR: {arr}")
        
    except Exception as e:
        logger.error(f"Error calculating revenue metrics: {str(e)}")
        db.rollback()
    finally:
        db.close()
