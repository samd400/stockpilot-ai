import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.core.deps import get_current_user, require_crm_role, require_any_role
from app.models.customer import Customer
from app.models.customer_loyalty import CustomerLoyalty
from app.services.loyalty_service import add_points, redeem_points, get_loyalty

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("/")
def list_customers(search: Optional[str] = None, customer_type: Optional[str] = None,
                   skip: int = 0, limit: int = 50,
                   db: Session = Depends(get_db), user: Dict = Depends(require_any_role)):
    q = db.query(Customer).filter(Customer.tenant_id == user["tenant_id"],
                                   Customer.is_active == True)
    if search:
        q = q.filter(or_(Customer.name.ilike(f"%{search}%"),
                          Customer.phone.ilike(f"%{search}%"),
                          Customer.email.ilike(f"%{search}%")))
    if customer_type:
        q = q.filter(Customer.customer_type == customer_type)
    customers = q.order_by(Customer.created_at.desc()).offset(skip).limit(limit).all()
    return [_customer_dict(c) for c in customers]


@router.post("/", status_code=201)
def create_customer(payload: Dict[str, Any], db: Session = Depends(get_db),
                    user: Dict = Depends(require_crm_role)):
    if payload.get("phone"):
        existing = db.query(Customer).filter(Customer.phone == payload["phone"],
                                              Customer.tenant_id == user["tenant_id"]).first()
        if existing:
            raise HTTPException(status_code=409, detail="Phone already registered")
    customer = Customer(
        id=uuid.uuid4(), tenant_id=user["tenant_id"],
        **{k: v for k, v in payload.items() if hasattr(Customer, k) and k not in ("id", "tenant_id")}
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return _customer_dict(customer)


@router.get("/{customer_id}")
def get_customer(customer_id: str, db: Session = Depends(get_db),
                 user: Dict = Depends(require_any_role)):
    customer = db.query(Customer).filter(Customer.id == customer_id,
                                          Customer.tenant_id == user["tenant_id"]).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    data = _customer_dict(customer)
    loyalty = get_loyalty(db, customer_id)
    if loyalty:
        data["loyalty"] = {"points": loyalty.points, "tier": loyalty.tier,
                           "total_spent": loyalty.total_spent}
    return data


@router.patch("/{customer_id}")
def update_customer(customer_id: str, payload: Dict[str, Any], db: Session = Depends(get_db),
                    user: Dict = Depends(require_crm_role)):
    customer = db.query(Customer).filter(Customer.id == customer_id,
                                          Customer.tenant_id == user["tenant_id"]).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    protected = {"id", "tenant_id", "created_at"}
    for k, v in payload.items():
        if k not in protected and hasattr(customer, k):
            setattr(customer, k, v)
    db.commit()
    db.refresh(customer)
    return _customer_dict(customer)


@router.delete("/{customer_id}", status_code=200)
def delete_customer(customer_id: str, db: Session = Depends(get_db),
                    user: Dict = Depends(require_crm_role)):
    customer = db.query(Customer).filter(Customer.id == customer_id,
                                          Customer.tenant_id == user["tenant_id"]).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer.is_active = False
    db.commit()
    return {"message": "Customer deactivated"}


@router.post("/{customer_id}/loyalty/add-points")
def add_loyalty_points(customer_id: str, payload: Dict[str, Any],
                        db: Session = Depends(get_db), user: Dict = Depends(require_any_role)):
    loyalty = add_points(db, user["tenant_id"], customer_id, payload.get("amount_spent", 0))
    return {"points": loyalty.points, "tier": loyalty.tier, "total_spent": loyalty.total_spent}


@router.post("/{customer_id}/loyalty/redeem")
def redeem_loyalty_points(customer_id: str, payload: Dict[str, Any],
                           db: Session = Depends(get_db), user: Dict = Depends(require_any_role)):
    try:
        discount = redeem_points(db, user["tenant_id"], customer_id, payload.get("points", 0))
        return {"discount_amount": discount, "points_redeemed": payload.get("points", 0)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/internal/by-phone/{phone}")
def get_by_phone(phone: str, tenant_id: str, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.phone == phone,
                                          Customer.tenant_id == tenant_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return _customer_dict(customer)


def _customer_dict(c: Customer) -> Dict:
    return {
        "id": str(c.id), "name": c.name, "email": c.email, "phone": c.phone,
        "address": c.address, "city": c.city, "country": c.country,
        "customer_type": c.customer_type, "total_purchases": c.total_purchases,
        "is_active": c.is_active, "created_at": c.created_at.isoformat(),
    }
