from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserRoleCreate(BaseModel):
    user_id: UUID
    role: str  # ADMIN, MANAGER, STAFF, VIEWER
    branch_id: Optional[UUID] = None


class UserRoleUpdate(BaseModel):
    role: Optional[str] = None
    branch_id: Optional[UUID] = None


class UserRoleResponse(BaseModel):
    id: UUID
    user_id: UUID
    role: str
    branch_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
