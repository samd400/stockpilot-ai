from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserSubscriptionCreate(BaseModel):
    subscription_plan_id: UUID
    payment_method: Optional[str] = None


class UserSubscriptionResponse(BaseModel):
    id: UUID
    user_id: UUID
    subscription_plan_id: UUID
    
    status: str
    
    start_date: datetime
    end_date: datetime
    renewal_date: datetime
    
    amount_paid: float
    payment_method: Optional[str]
    stripe_subscription_id: Optional[str]
    razorpay_subscription_id: Optional[str]
    
    auto_renew: str
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
