import os
from typing import Dict, Any, Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey-stockpilot-change-in-production-32chars")
ALGORITHM = "HS256"
SERVICE_TOKEN = os.getenv("SERVICE_TOKEN", "internal-service-secret-change-me")


def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate credentials",
                            headers={"WWW-Authenticate": "Bearer"})


def verify_service_token(token: str) -> bool:
    return token == SERVICE_TOKEN
