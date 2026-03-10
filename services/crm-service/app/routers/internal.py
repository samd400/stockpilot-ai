from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import verify_service_token
from app.models.customer import Customer
from app.services import loyalty_service

router = APIRouter(prefix="/internal", tags=["Internal"])


@router.get("/customers/{customer_id}")
def get_customer_internal(customer_id: str, db: Session = Depends(get_db),
                           _: bool = Depends(verify_service_token)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"id": str(customer.id), "name": customer.name, "phone": customer.phone,
            "email": customer.email, "customer_type": customer.customer_type}


@router.post("/customers/loyalty/add-points")
def add_loyalty_points_internal(payload: Dict[str, Any], db: Session = Depends(get_db),
                                 _: bool = Depends(verify_service_token)):
    loyalty = loyalty_service.add_points(
        db, payload["tenant_id"], payload["customer_id"], payload["amount_spent"]
    )
    return {"points": loyalty.points, "tier": loyalty.tier}


@router.get("/customers/by-phone/{phone}")
def get_by_phone_internal(phone: str, tenant_id: str, db: Session = Depends(get_db),
                           _: bool = Depends(verify_service_token)):
    customer = db.query(Customer).filter(Customer.phone == phone,
                                          Customer.tenant_id == tenant_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"id": str(customer.id), "name": customer.name, "phone": customer.phone}
