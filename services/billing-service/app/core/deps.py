import os
from typing import Dict, Any
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token, verify_service_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://auth-service:8001/auth/login")

BILLING_ROLES = {"admin", "billing_staff", "manager"}
VIEWER_ROLES = {"admin", "billing_staff", "manager", "viewer"}


def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    payload = decode_token(token)
    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    role = payload.get("role", "viewer")
    if not user_id or not tenant_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return {"user_id": user_id, "tenant_id": tenant_id, "role": role}


def require_billing_role(user: Dict = Depends(get_current_user)) -> Dict:
    if user["role"] not in BILLING_ROLES:
        raise HTTPException(status_code=403,
                            detail="Billing staff, manager, or admin access required")
    return user


def require_any_role(user: Dict = Depends(get_current_user)) -> Dict:
    return user  # Any authenticated user


def verify_internal_token(x_service_token: str = Header(None)) -> bool:
    if not x_service_token or not verify_service_token(x_service_token):
        raise HTTPException(status_code=403, detail="Invalid service token")
    return True
