from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CustomerBase(BaseModel):
    name: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

class CustomerResponse(CustomerBase):
    id: str
    user_id: str
    loyalty_points: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Alias for backward compatibility
Customer = CustomerResponse
