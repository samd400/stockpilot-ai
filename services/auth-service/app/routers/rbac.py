from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserRoleEnum
from app.models.user_role import UserRole
from app.routers.auth import get_current_user
from app.schemas.auth import RoleAssignRequest, RoleResponse

router = APIRouter(prefix="/rbac", tags=["RBAC"])

AVAILABLE_PERMISSIONS = [
    "inventory:read", "inventory:write", "inventory:delete",
    "orders:read", "orders:write", "orders:delete",
    "customers:read", "customers:write", "customers:delete",
    "suppliers:read", "suppliers:write",
    "invoices:read", "invoices:write", "invoices:delete",
    "billing:read", "billing:write",
    "reports:read", "analytics:read",
    "users:read", "users:write", "users:delete",
    "settings:read", "settings:write",
    "agents:read", "agents:trigger",
]

ROLE_DEFAULTS = {
    "admin": AVAILABLE_PERMISSIONS,
    "manager": ["inventory:read", "inventory:write", "orders:read", "orders:write",
                 "customers:read", "customers:write", "invoices:read", "invoices:write",
                 "reports:read", "analytics:read", "users:read", "suppliers:read"],
    "billing_staff": ["invoices:read", "invoices:write", "billing:read", "billing:write",
                      "orders:read", "customers:read", "reports:read"],
    "inventory_staff": ["inventory:read", "inventory:write", "suppliers:read", "orders:read"],
    "crm_staff": ["customers:read", "customers:write", "orders:read", "orders:write",
                  "invoices:read"],
    "viewer": ["inventory:read", "orders:read", "customers:read", "reports:read"],
}


def _require_admin(u: User):
    if u.role != UserRoleEnum.admin:
        raise HTTPException(status_code=403, detail="Admin access required")


@router.get("/roles", response_model=List[RoleResponse])
def list_roles(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    roles = db.query(UserRole).filter(UserRole.tenant_id == current_user.tenant_id).all()
    return [RoleResponse(id=str(r.id), user_id=str(r.user_id), tenant_id=str(r.tenant_id),
                         role=r.role, permissions=r.permissions or [],
                         created_at=r.created_at) for r in roles]


@router.post("/roles", response_model=RoleResponse, status_code=201)
def assign_role(payload: RoleAssignRequest, current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    _require_admin(current_user)
    target = db.query(User).filter(User.id == payload.user_id,
                                    User.tenant_id == current_user.tenant_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    existing = db.query(UserRole).filter(UserRole.user_id == payload.user_id,
                                          UserRole.tenant_id == current_user.tenant_id,
                                          UserRole.role == payload.role).first()
    if existing:
        raise HTTPException(status_code=409, detail="Role already assigned")
    perms = payload.permissions if payload.permissions else ROLE_DEFAULTS.get(payload.role, [])
    role = UserRole(tenant_id=current_user.tenant_id, user_id=payload.user_id,
                    role=payload.role, permissions=perms)
    db.add(role)
    db.commit()
    db.refresh(role)
    return RoleResponse(id=str(role.id), user_id=str(role.user_id), tenant_id=str(role.tenant_id),
                        role=role.role, permissions=role.permissions or [],
                        created_at=role.created_at)


@router.delete("/roles/{role_id}", status_code=200)
def remove_role(role_id: str, current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    _require_admin(current_user)
    role = db.query(UserRole).filter(UserRole.id == role_id,
                                      UserRole.tenant_id == current_user.tenant_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    db.delete(role)
    db.commit()
    return {"message": "Role removed"}


@router.get("/permissions")
def list_permissions(current_user: User = Depends(get_current_user)):
    return {"available_permissions": AVAILABLE_PERMISSIONS, "role_defaults": ROLE_DEFAULTS}
