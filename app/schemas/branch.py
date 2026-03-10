from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class BranchCreate(BaseModel):
    name: str
    location: str
    address: Optional[str] = None
    phone: Optional[str] = None
    manager_name: Optional[str] = None


class BranchUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    manager_name: Optional[str] = None
    is_active: Optional[str] = None


class BranchResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    location: str
    address: Optional[str]
    phone: Optional[str]
    manager_name: Optional[str]
    is_active: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
