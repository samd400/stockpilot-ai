import re
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator


ALLOWED_ROLES = {"admin", "staff", "manager", "billing_staff", "inventory_staff", "crm_staff", "viewer"}
ALLOWED_TAX_REGIONS = {"india_gst", "gcc_vat", "eu_vat"}


class TenantRegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    business_name: Optional[str] = None
    country_code: str = "IN"
    currency: str = "INR"
    tax_region: str = "india_gst"
    timezone: str = "Asia/Kolkata"
    subdomain: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Must contain at least one uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Must contain at least one digit")
        return v

    @field_validator("subdomain")
    @classmethod
    def validate_subdomain(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9][a-z0-9\-]{1,61}[a-z0-9]$", v):
            raise ValueError("Subdomain: lowercase alphanumeric/hyphens, 3-63 chars")
        return v

    @field_validator("tax_region")
    @classmethod
    def validate_tax_region(cls, v: str) -> str:
        if v not in ALLOWED_TAX_REGIONS:
            raise ValueError(f"tax_region must be one of {ALLOWED_TAX_REGIONS}")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: str
    user_id: str
    role: str


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    role: str = "viewer"
    business_name: Optional[str] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ALLOWED_ROLES:
            raise ValueError(f"role must be one of {ALLOWED_ROLES}")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    tenant_id: str
    business_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class TenantResponse(BaseModel):
    id: str
    name: str
    country_code: str
    currency: str
    tax_region: str
    timezone: str
    subdomain: str
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    business_address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    logo_url: Optional[str] = None
    invoice_prefix: str
    allow_autonomous_agents: bool
    allow_dynamic_pricing: bool
    allow_auto_procurement: bool
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class TenantUpdateRequest(BaseModel):
    name: Optional[str] = None
    country_code: Optional[str] = None
    currency: Optional[str] = None
    tax_region: Optional[str] = None
    timezone: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    business_address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    logo_url: Optional[str] = None
    invoice_prefix: Optional[str] = None
    allow_autonomous_agents: Optional[bool] = None
    allow_dynamic_pricing: Optional[bool] = None
    allow_auto_procurement: Optional[bool] = None

    @field_validator("tax_region")
    @classmethod
    def validate_tax_region(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_TAX_REGIONS:
            raise ValueError(f"tax_region must be one of {ALLOWED_TAX_REGIONS}")
        return v


class UserUpdateRequest(BaseModel):
    business_name: Optional[str] = None
    owner_name: Optional[str] = None
    phone: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    business_address: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_ROLES:
            raise ValueError(f"role must be one of {ALLOWED_ROLES}")
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("New password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Must contain at least one uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Must contain at least one digit")
        return v


class RoleAssignRequest(BaseModel):
    user_id: str
    role: str
    permissions: Optional[List[str]] = []

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"admin", "manager", "billing_staff", "inventory_staff", "crm_staff", "viewer"}
        if v not in allowed:
            raise ValueError(f"role must be one of {allowed}")
        return v


class RoleResponse(BaseModel):
    id: str
    user_id: str
    tenant_id: str
    role: str
    permissions: List[str]
    created_at: datetime
    model_config = {"from_attributes": True}
