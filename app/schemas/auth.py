from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: Optional[str] = None


class TenantRegisterRequest(BaseModel):
    """Register a new tenant + admin user."""
    tenant_name: str
    subdomain: str
    owner_name: str
    email: EmailStr
    password: str
    country_code: str = "IN"
    currency: str = "INR"
    tax_region: str = "india_gst"
    timezone: str = "Asia/Kolkata"
    phone: Optional[str] = None
    gst_number: Optional[str] = None
    business_address: Optional[str] = None


class TenantResponse(BaseModel):
    id: str
    name: str
    subdomain: str
    country_code: str
    currency: str
    tax_region: str
    timezone: str
    is_active: bool

    class Config:
        from_attributes = True
