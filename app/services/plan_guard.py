from fastapi import HTTPException
from datetime import datetime
from app.models.product import Product
from app.models.tenant import Tenant


def check_subscription_active(user):
    """Check if user/tenant subscription is active."""
    # Check tenant-level expiry first, fallback to user-level
    if hasattr(user, 'tenant') and user.tenant and user.tenant.subscription_expiry:
        if user.tenant.subscription_expiry < datetime.utcnow():
            raise HTTPException(
                status_code=403,
                detail="Subscription expired. Please renew your plan."
            )
    elif user.subscription_expiry:
        if user.subscription_expiry < datetime.utcnow():
            raise HTTPException(
                status_code=403,
                detail="Subscription expired. Please renew your plan."
            )


def check_product_limit(user, db):
    """Check product limit scoped to tenant."""
    check_subscription_active(user)

    tenant_id = user.tenant_id if hasattr(user, 'tenant_id') else None

    if tenant_id:
        product_count = db.query(Product).filter(
            Product.tenant_id == tenant_id
        ).count()
    else:
        product_count = db.query(Product).filter(
            Product.user_id == user.id
        ).count()

    # Check plan limit (prefer tenant subscription, fallback to user)
    plan = None
    if hasattr(user, 'tenant') and user.tenant and user.tenant.subscription:
        plan = user.tenant.subscription
    elif user.subscription:
        plan = user.subscription

    if plan and product_count >= plan.max_products:
        raise HTTPException(
            status_code=403,
            detail="Product limit reached. Upgrade your plan."
        )
