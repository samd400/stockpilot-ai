from app.core.database import SessionLocal
from app.models.subscription_plan import SubscriptionPlan


def seed_subscription_plans():
    db = SessionLocal()

    existing = db.query(SubscriptionPlan).count()
    if existing > 0:
        print("Plans already exist.")
        db.close()
        return

    plans = [
        SubscriptionPlan(
            name="Free",
            price=0,
            max_products=10,
            max_invoices_per_month=50
        ),
        SubscriptionPlan(
            name="Pro",
            price=999,
            max_products=100,
            max_invoices_per_month=500
        ),
        SubscriptionPlan(
            name="Enterprise",
            price=4999,
            max_products=10000,
            max_invoices_per_month=100000
        )
    ]

    for plan in plans:
        db.add(plan)

    db.commit()
    db.close()

    print("Subscription plans seeded successfully!")


if __name__ == "__main__":
    seed_subscription_plans()
