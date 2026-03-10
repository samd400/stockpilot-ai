import os
from typing import Dict, Any
from fastapi import Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey-stockpilot-change-in-production-32chars")
ALGORITHM = "HS256"
SERVICE_TOKEN = os.getenv("SERVICE_TOKEN", "internal-service-secret-change-me")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://auth-service:8001/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    if not user_id or not tenant_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return {"user_id": user_id, "tenant_id": tenant_id, "role": payload.get("role", "viewer")}


def require_any_role(user: Dict = Depends(get_current_user)) -> Dict:
    return user


def require_admin_or_manager(user: Dict = Depends(get_current_user)) -> Dict:
    if user["role"] not in {"admin", "manager"}:
        raise HTTPException(status_code=403, detail="Admin or manager required")
    return user


def verify_service_token(x_service_token: str = Header(None)) -> bool:
    if not x_service_token or x_service_token != SERVICE_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid service token")
    return True
