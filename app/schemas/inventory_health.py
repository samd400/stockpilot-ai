from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class InventoryHealthResponse(BaseModel):
    id: UUID
    user_id: UUID
    product_id: UUID
    
    turnover_ratio: float
    stock_out_frequency: float
    dead_stock_percentage: float
    carrying_cost_ratio: float
    
    health_score: float
    status: str
    recommendations: Optional[str]
    
    calculated_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
