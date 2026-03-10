from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class CustomerLoyaltyResponse(BaseModel):
    id: UUID
    customer_id: str
    user_id: UUID
    
    total_spent: float
    loyalty_points: float
    tier: str
    
    discount_percentage: float
    points_multiplier: float
    
    last_purchase_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
