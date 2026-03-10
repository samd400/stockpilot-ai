from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class DynamicPriceResponse(BaseModel):
    id: UUID
    user_id: UUID
    product_id: UUID
    
    base_price: float
    current_price: float
    
    demand_multiplier: float
    stock_multiplier: float
    seasonality_multiplier: float
    competitor_multiplier: float
    
    min_price: float
    max_price: float
    
    last_updated: datetime
    created_at: datetime

    class Config:
        from_attributes = True
