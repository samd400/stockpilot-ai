from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class DemandForecastResponse(BaseModel):
    id: UUID
    user_id: UUID
    product_id: UUID
    
    forecast_date: datetime
    predicted_quantity: int
    confidence_level: float
    
    historical_avg_sales: float
    trend: Optional[str]
    seasonality_factor: float
    
    recommended_stock: int
    reorder_urgency: str
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
