from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.core.auth_dependency import get_current_user
from app.schemas.user import UserCreate, UserResponse
import uuid
import re



router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Auto-create tenant for new registration
    subdomain = re.sub(r'[^a-z0-9-]', '-', user.business_name.lower().strip())[:50]
    subdomain = re.sub(r'-+', '-', subdomain).strip('-') or "tenant"
    # Ensure unique subdomain
    base_subdomain = subdomain
    counter = 1
    while db.query(Tenant).filter(Tenant.subdomain == subdomain).first():
        subdomain = f"{base_subdomain}-{counter}"
        counter += 1

    tenant = Tenant(
        id=uuid.uuid4(),
        name=user.business_name,
        subdomain=subdomain,
    )
    db.add(tenant)
    db.flush()

    new_user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        business_name=user.business_name,
        owner_name=user.owner_name,
        email=user.email,
        password_hash=hash_password(user.password),
        phone=user.phone,
        role=UserRole.ADMIN,
    )

    db.add(new_user)

    # Link tenant back to owner
    tenant.owner_user_id = new_user.id

    db.commit()
    db.refresh(new_user)

    return new_user

@router.get("/me")
def get_me(current_user = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "business_name": current_user.business_name
    }