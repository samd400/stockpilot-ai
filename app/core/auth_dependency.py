from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.security import SECRET_KEY, ALGORITHM
from app.core.database import SessionLocal
from app.models.user import User
from app.models.tenant import Tenant
from sqlalchemy.orm import Session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    db: Session = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    db.close()

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def get_current_tenant_id(token: str = Depends(oauth2_scheme)) -> str:
    """Extract tenant_id from JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        tenant_id: str = payload.get("tenant_id")
        if tenant_id is None:
            # Fallback: get tenant_id from user
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            db = SessionLocal()
            user = db.query(User).filter(User.id == user_id).first()
            db.close()
            if user and user.tenant_id:
                return str(user.tenant_id)
            raise HTTPException(status_code=401, detail="No tenant associated")
        return tenant_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_tenant(token: str = Depends(oauth2_scheme)):
    """Get the full Tenant object from JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        tenant_id: str = payload.get("tenant_id")
        user_id: str = payload.get("sub")

        db = SessionLocal()
        if tenant_id:
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        elif user_id:
            user = db.query(User).filter(User.id == user_id).first()
            tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first() if user else None
        else:
            tenant = None
        db.close()

        if tenant is None:
            raise HTTPException(status_code=401, detail="Tenant not found")
        return tenant
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
