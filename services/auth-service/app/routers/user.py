from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.models.user import User, UserRoleEnum
from app.models.audit_log import AuditLog
from app.routers.auth import get_current_user
from app.schemas.auth import UserCreateRequest, UserResponse, UserUpdateRequest, ChangePasswordRequest

router = APIRouter(prefix="/users", tags=["Users"])


def _require_admin(u: User):
    if u.role != UserRoleEnum.admin:
        raise HTTPException(status_code=403, detail="Admin access required")


def _log(db, tenant_id, action, user_id=None, ip=None, ua=None, details=None):
    db.add(AuditLog(tenant_id=tenant_id, user_id=user_id, action=action,
                    ip_address=ip, user_agent=ua, details=details))


@router.get("", response_model=List[UserResponse])
def list_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    users = db.query(User).filter(User.tenant_id == current_user.tenant_id).all()
    return [UserResponse(id=str(u.id), email=u.email, role=u.role.value,
                         tenant_id=str(u.tenant_id), business_name=u.business_name,
                         is_active=u.is_active, created_at=u.created_at) for u in users]


@router.post("", response_model=UserResponse, status_code=201)
def create_user(payload: UserCreateRequest, request: Request,
                current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    new_user = User(
        tenant_id=current_user.tenant_id, email=payload.email,
        password_hash=hash_password(payload.password),
        role=UserRoleEnum(payload.role), business_name=payload.business_name,
    )
    db.add(new_user)
    ip = request.client.host if request.client else None
    _log(db, current_user.tenant_id, "REGISTER", current_user.id, ip,
         request.headers.get("user-agent"), {"created_user": payload.email})
    db.commit()
    db.refresh(new_user)
    return UserResponse(id=str(new_user.id), email=new_user.email, role=new_user.role.value,
                        tenant_id=str(new_user.tenant_id), business_name=new_user.business_name,
                        is_active=new_user.is_active, created_at=new_user.created_at)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, current_user: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    if str(current_user.id) != user_id and current_user.role != UserRoleEnum.admin:
        raise HTTPException(status_code=403, detail="Access denied")
    user = db.query(User).filter(User.id == user_id,
                                  User.tenant_id == current_user.tenant_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(id=str(user.id), email=user.email, role=user.role.value,
                        tenant_id=str(user.tenant_id), business_name=user.business_name,
                        is_active=user.is_active, created_at=user.created_at)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: str, payload: UserUpdateRequest, request: Request,
                current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    is_self = str(current_user.id) == user_id
    is_admin = current_user.role == UserRoleEnum.admin
    if not is_self and not is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    user = db.query(User).filter(User.id == user_id,
                                  User.tenant_id == current_user.tenant_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    update_data = payload.model_dump(exclude_unset=True)
    if "role" in update_data:
        if not is_admin:
            raise HTTPException(status_code=403, detail="Only admins can change roles")
        update_data["role"] = UserRoleEnum(update_data["role"])
    if "is_active" in update_data and not is_admin:
        raise HTTPException(status_code=403, detail="Only admins can change active status")
    for k, v in update_data.items():
        setattr(user, k, v)
    ip = request.client.host if request.client else None
    _log(db, current_user.tenant_id, "UPDATE_PROFILE", current_user.id, ip,
         request.headers.get("user-agent"), {"user_id": user_id, "fields": list(update_data.keys())})
    db.commit()
    db.refresh(user)
    return UserResponse(id=str(user.id), email=user.email, role=user.role.value,
                        tenant_id=str(user.tenant_id), business_name=user.business_name,
                        is_active=user.is_active, created_at=user.created_at)


@router.delete("/{user_id}", status_code=200)
def deactivate_user(user_id: str, request: Request,
                    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    if str(current_user.id) == user_id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    user = db.query(User).filter(User.id == user_id,
                                  User.tenant_id == current_user.tenant_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    ip = request.client.host if request.client else None
    _log(db, current_user.tenant_id, "ROLE_CHANGE", current_user.id, ip,
         request.headers.get("user-agent"), {"deactivated": user_id})
    db.commit()
    return {"message": "User deactivated"}


@router.patch("/{user_id}/password", status_code=200)
def change_password(user_id: str, payload: ChangePasswordRequest, request: Request,
                    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    is_self = str(current_user.id) == user_id
    is_admin = current_user.role == UserRoleEnum.admin
    if not is_self and not is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    user = db.query(User).filter(User.id == user_id,
                                  User.tenant_id == current_user.tenant_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if is_self and not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.password_hash = hash_password(payload.new_password)
    ip = request.client.host if request.client else None
    _log(db, current_user.tenant_id, "CHANGE_PASSWORD", current_user.id, ip,
         request.headers.get("user-agent"), {"target": user_id})
    db.commit()
    return {"message": "Password changed successfully"}
