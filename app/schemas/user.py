from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class UserCreate(BaseModel):
    business_name: str
    owner_name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    business_name: Optional[str] = None
    owner_name: Optional[str] = None
    email: str
    phone: Optional[str] = None

    class Config:
        from_attributes = True
