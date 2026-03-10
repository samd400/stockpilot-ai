import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, hash_password, decode_token
from app.models.tenant import Tenant
from app.models.user import User, UserRoleEnum
from app.models.audit_log import AuditLog
from app.schemas.auth import TenantRegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

_redis_client = None
try:
    import redis as redis_lib
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    _redis_client = redis_lib.from_url(REDIS_URL, decode_responses=True)
    _redis_client.ping()
except Exception:
    _redis_client = None


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    if _redis_client:
        try:
            if _redis_client.get(f"blacklist:{token}"):
                raise HTTPException(status_code=401, detail="Token invalidated",
                                    headers={"WWW-Authenticate": "Bearer"})
        except Exception:
            pass
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload",
                            headers={"WWW-Authenticate": "Bearer"})
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive",
                            headers={"WWW-Authenticate": "Bearer"})
    return user


def _log_audit(db, tenant_id, action, user_id=None, ip=None, ua=None, details=None):
    db.add(AuditLog(
        tenant_id=tenant_id, user_id=user_id, action=action,
        ip_address=ip, user_agent=ua, details=details,
    ))


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: TenantRegisterRequest, request: Request, db: Session = Depends(get_db)):
    if db.query(Tenant).filter(Tenant.subdomain == payload.subdomain).first():
        raise HTTPException(status_code=409, detail="Subdomain already taken")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    try:
        tenant = Tenant(
            name=payload.name, country_code=payload.country_code,
            currency=payload.currency, tax_region=payload.tax_region,
            timezone=payload.timezone, subdomain=payload.subdomain, email=payload.email,
        )
        db.add(tenant)
        db.flush()
        user = User(
            tenant_id=tenant.id, email=payload.email,
            password_hash=hash_password(payload.password),
            role=UserRoleEnum.admin, business_name=payload.business_name,
        )
        db.add(user)
        db.flush()
        tenant.owner_user_id = user.id
        ip = request.client.host if request.client else None
        _log_audit(db, tenant.id, "REGISTER", user.id, ip, request.headers.get("user-agent"),
                   {"email": payload.email})
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {e}")
    token = create_access_token(str(user.id), str(tenant.id), user.role.value)
    return TokenResponse(access_token=token, tenant_id=str(tenant.id),
                         user_id=str(user.id), role=user.role.value)


@router.post("/login", response_model=TokenResponse)
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(),
          db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username, User.is_active == True).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password",
                            headers={"WWW-Authenticate": "Bearer"})
    ip = request.client.host if request.client else None
    _log_audit(db, user.tenant_id, "LOGIN", user.id, ip, request.headers.get("user-agent"))
    db.commit()
    token = create_access_token(str(user.id), str(user.tenant_id), user.role.value)
    return TokenResponse(access_token=token, tenant_id=str(user.tenant_id),
                         user_id=str(user.id), role=user.role.value)


@router.post("/refresh", response_model=TokenResponse)
def refresh(current_user: User = Depends(get_current_user)):
    token = create_access_token(str(current_user.id), str(current_user.tenant_id),
                                current_user.role.value)
    return TokenResponse(access_token=token, tenant_id=str(current_user.tenant_id),
                         user_id=str(current_user.id), role=current_user.role.value)


@router.post("/logout", status_code=200)
def logout(request: Request, token: str = Depends(oauth2_scheme),
           current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if _redis_client:
        try:
            payload = decode_token(token)
            exp = payload.get("exp")
            if exp:
                ttl = int(exp - datetime.utcnow().timestamp())
                if ttl > 0:
                    _redis_client.setex(f"blacklist:{token}", ttl, "1")
        except Exception:
            pass
    ip = request.client.host if request.client else None
    _log_audit(db, current_user.tenant_id, "LOGOUT", current_user.id, ip,
               request.headers.get("user-agent"))
    db.commit()
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(id=str(current_user.id), email=current_user.email,
                        role=current_user.role.value, tenant_id=str(current_user.tenant_id),
                        business_name=current_user.business_name,
                        is_active=current_user.is_active, created_at=current_user.created_at)
