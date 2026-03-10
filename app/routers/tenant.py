from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
import re

from app.core.dependencies import get_db
from app.core.security import hash_password, create_access_token
from app.core.auth_dependency import get_current_user, get_current_tenant
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.schemas.auth import TenantRegisterRequest, TenantResponse

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.post("/register", response_model=dict)
def register_tenant(
    req: TenantRegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new tenant and create the admin user."""
    # Validate subdomain format
    if not re.match(r'^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$', req.subdomain):
        raise HTTPException(status_code=400, detail="Invalid subdomain format. Use lowercase letters, numbers, hyphens.")

    # Check subdomain uniqueness
    existing = db.query(Tenant).filter(Tenant.subdomain == req.subdomain).first()
    if existing:
        raise HTTPException(status_code=400, detail="Subdomain already taken")

    # Check email uniqueness
    existing_user = db.query(User).filter(User.email == req.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create tenant
    tenant = Tenant(
        id=uuid.uuid4(),
        name=req.tenant_name,
        subdomain=req.subdomain,
        country_code=req.country_code,
        currency=req.currency,
        tax_region=req.tax_region,
        timezone=req.timezone,
        phone=req.phone,
        gst_number=req.gst_number,
        business_address=req.business_address,
        email=req.email,
    )
    db.add(tenant)
    db.flush()

    # Create admin user
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email=req.email,
        password_hash=hash_password(req.password),
        role=UserRole.ADMIN,
        owner_name=req.owner_name,
        business_name=req.tenant_name,
    )
    db.add(user)
    db.flush()

    # Set owner
    tenant.owner_user_id = user.id
    db.commit()
    db.refresh(tenant)
    db.refresh(user)

    # Create JWT token
    token = create_access_token({
        "sub": str(user.id),
        "tenant_id": str(tenant.id),
        "role": user.role.value,
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "tenant_id": str(tenant.id),
        "tenant": {
            "id": str(tenant.id),
            "name": tenant.name,
            "subdomain": tenant.subdomain,
            "country_code": tenant.country_code,
            "currency": tenant.currency,
            "tax_region": tenant.tax_region,
        }
    }


@router.get("/me", response_model=TenantResponse)
def get_my_tenant(
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get current tenant info."""
    return current_tenant


@router.put("/me")
def update_my_tenant(
    updates: dict,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Update current tenant info."""
    allowed_fields = {"name", "phone", "gst_number", "pan_number", "business_address", "logo_url", "invoice_prefix", "timezone"}
    for key, value in updates.items():
        if key in allowed_fields:
            setattr(current_tenant, key, value)

    db.merge(current_tenant)
    db.commit()
    return {"message": "Tenant updated successfully"}
