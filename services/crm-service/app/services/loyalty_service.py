"""Customer loyalty points and tier management."""
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.models.customer_loyalty import CustomerLoyalty
import uuid

TIER_THRESHOLDS = {"bronze": 0, "silver": 1000, "gold": 5000, "platinum": 20000}
POINTS_PER_CURRENCY_UNIT = 1  # 1 point per currency unit spent
POINT_VALUE = 0.01  # 1 point = 0.01 currency unit


def _get_or_create_loyalty(db: Session, tenant_id: str, customer_id: str) -> CustomerLoyalty:
    loyalty = db.query(CustomerLoyalty).filter(
        CustomerLoyalty.customer_id == customer_id
    ).first()
    if not loyalty:
        loyalty = CustomerLoyalty(
            id=uuid.uuid4(), tenant_id=tenant_id, customer_id=customer_id,
            points=0, tier="bronze", total_spent=0
        )
        db.add(loyalty)
        db.flush()
    return loyalty


def _calculate_tier(total_spent: float) -> str:
    if total_spent >= TIER_THRESHOLDS["platinum"]:
        return "platinum"
    elif total_spent >= TIER_THRESHOLDS["gold"]:
        return "gold"
    elif total_spent >= TIER_THRESHOLDS["silver"]:
        return "silver"
    return "bronze"


def add_points(db: Session, tenant_id: str, customer_id: str, amount_spent: float) -> CustomerLoyalty:
    loyalty = _get_or_create_loyalty(db, tenant_id, customer_id)
    points_earned = int(amount_spent * POINTS_PER_CURRENCY_UNIT)
    loyalty.points += points_earned
    loyalty.total_spent += amount_spent
    loyalty.tier = _calculate_tier(loyalty.total_spent)

    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer:
        customer.total_purchases += amount_spent
    db.commit()
    return loyalty


def redeem_points(db: Session, tenant_id: str, customer_id: str, points: int) -> float:
    loyalty = db.query(CustomerLoyalty).filter(
        CustomerLoyalty.customer_id == customer_id
    ).first()
    if not loyalty or loyalty.points < points:
        raise ValueError(f"Insufficient points. Available: {loyalty.points if loyalty else 0}")
    discount = points * POINT_VALUE
    loyalty.points -= points
    db.commit()
    return round(discount, 2)


def get_loyalty(db: Session, customer_id: str):
    return db.query(CustomerLoyalty).filter(
        CustomerLoyalty.customer_id == customer_id
    ).first()
