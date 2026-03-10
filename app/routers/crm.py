from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user
from app.models.user import User
from app.models.customer import Customer
from app.models.customer_loyalty import CustomerLoyalty, LoyaltyTierType
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.schemas.customer_loyalty import CustomerLoyaltyResponse
from typing import List

router = APIRouter(prefix="/crm", tags=["CRM"])


@router.post("/customers", response_model=CustomerResponse)
def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new customer"""
    new_customer = Customer(
        user_id=str(current_user.id),
        name=customer.name,
        phone_number=customer.phone_number,
        email=customer.email,
        address=customer.address
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    
    # Create loyalty record
    loyalty = CustomerLoyalty(
        customer_id=new_customer.id,
        user_id=current_user.id,
        tier=LoyaltyTierType.BRONZE
    )
    db.add(loyalty)
    db.commit()
    
    return new_customer


@router.get("/customers", response_model=List[CustomerResponse])
def list_customers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all customers"""
    customers = db.query(Customer).filter(
        Customer.user_id == str(current_user.id)
    ).all()
    return customers


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific customer"""
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.user_id == str(current_user.id)
    ).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return customer


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: str,
    customer_update: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a customer"""
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.user_id == str(current_user.id)
    ).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    update_data = customer_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(customer, key, value)
    
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/loyalty/{customer_id}", response_model=CustomerLoyaltyResponse)
def get_customer_loyalty(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get customer loyalty information"""
    loyalty = db.query(CustomerLoyalty).filter(
        CustomerLoyalty.customer_id == customer_id,
        CustomerLoyalty.user_id == current_user.id
    ).first()
    
    if not loyalty:
        raise HTTPException(status_code=404, detail="Loyalty record not found")
    
    return loyalty


@router.post("/loyalty/{customer_id}/add-points")
def add_loyalty_points(
    customer_id: str,
    points: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add loyalty points to a customer"""
    loyalty = db.query(CustomerLoyalty).filter(
        CustomerLoyalty.customer_id == customer_id,
        CustomerLoyalty.user_id == current_user.id
    ).first()
    
    if not loyalty:
        raise HTTPException(status_code=404, detail="Loyalty record not found")
    
    loyalty.loyalty_points += points
    
    # Update tier based on total spent
    if loyalty.total_spent >= 50000:
        loyalty.tier = LoyaltyTierType.PLATINUM
        loyalty.discount_percentage = 15.0
        loyalty.points_multiplier = 2.0
    elif loyalty.total_spent >= 25000:
        loyalty.tier = LoyaltyTierType.GOLD
        loyalty.discount_percentage = 10.0
        loyalty.points_multiplier = 1.5
    elif loyalty.total_spent >= 10000:
        loyalty.tier = LoyaltyTierType.SILVER
        loyalty.discount_percentage = 5.0
        loyalty.points_multiplier = 1.25
    
    db.commit()
    db.refresh(loyalty)
    
    return {
        "message": "Points added successfully",
        "loyalty": loyalty
    }


@router.post("/loyalty/{customer_id}/redeem-points")
def redeem_loyalty_points(
    customer_id: str,
    points: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Redeem loyalty points"""
    loyalty = db.query(CustomerLoyalty).filter(
        CustomerLoyalty.customer_id == customer_id,
        CustomerLoyalty.user_id == current_user.id
    ).first()
    
    if not loyalty:
        raise HTTPException(status_code=404, detail="Loyalty record not found")
    
    if loyalty.loyalty_points < points:
        raise HTTPException(status_code=400, detail="Insufficient loyalty points")
    
    loyalty.loyalty_points -= points
    
    db.commit()
    db.refresh(loyalty)
    
    return {
        "message": "Points redeemed successfully",
        "remaining_points": loyalty.loyalty_points
    }
