from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user
from app.models.user import User
from app.models.user_role import UserRole, RoleType
from app.schemas.user_role import UserRoleCreate, UserRoleUpdate, UserRoleResponse
from typing import List

router = APIRouter(prefix="/rbac", tags=["RBAC"])


@router.post("/roles", response_model=UserRoleResponse)
def assign_role(
    role_assignment: UserRoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign a role to a user (Admin only)"""
    
    # Check if current user is admin
    admin_role = db.query(UserRole).filter(
        UserRole.user_id == current_user.id,
        UserRole.role == RoleType.ADMIN
    ).first()
    
    if not admin_role:
        raise HTTPException(status_code=403, detail="Only admins can assign roles")
    
    # Check if user exists
    user = db.query(User).filter(User.id == role_assignment.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if role already exists
    existing_role = db.query(UserRole).filter(
        UserRole.user_id == role_assignment.user_id
    ).first()
    
    if existing_role:
        existing_role.role = role_assignment.role
        existing_role.branch_id = role_assignment.branch_id
        db.commit()
        db.refresh(existing_role)
        return existing_role
    
    # Create new role
    new_role = UserRole(
        user_id=role_assignment.user_id,
        role=role_assignment.role,
        branch_id=role_assignment.branch_id
    )
    
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    
    return new_role


@router.get("/roles/{user_id}", response_model=UserRoleResponse)
def get_user_role(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user role"""
    
    role = db.query(UserRole).filter(UserRole.user_id == user_id).first()
    
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return role


@router.get("/roles", response_model=List[UserRoleResponse])
def list_all_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all roles (Admin only)"""
    
    # Check if current user is admin
    admin_role = db.query(UserRole).filter(
        UserRole.user_id == current_user.id,
        UserRole.role == RoleType.ADMIN
    ).first()
    
    if not admin_role:
        raise HTTPException(status_code=403, detail="Only admins can view all roles")
    
    roles = db.query(UserRole).all()
    return roles


@router.put("/roles/{user_id}", response_model=UserRoleResponse)
def update_user_role(
    user_id: str,
    role_update: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user role (Admin only)"""
    
    # Check if current user is admin
    admin_role = db.query(UserRole).filter(
        UserRole.user_id == current_user.id,
        UserRole.role == RoleType.ADMIN
    ).first()
    
    if not admin_role:
        raise HTTPException(status_code=403, detail="Only admins can update roles")
    
    role = db.query(UserRole).filter(UserRole.user_id == user_id).first()
    
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    update_data = role_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(role, key, value)
    
    db.commit()
    db.refresh(role)
    
    return role


@router.delete("/roles/{user_id}")
def delete_user_role(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete user role (Admin only)"""
    
    # Check if current user is admin
    admin_role = db.query(UserRole).filter(
        UserRole.user_id == current_user.id,
        UserRole.role == RoleType.ADMIN
    ).first()
    
    if not admin_role:
        raise HTTPException(status_code=403, detail="Only admins can delete roles")
    
    role = db.query(UserRole).filter(UserRole.user_id == user_id).first()
    
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    db.delete(role)
    db.commit()
    
    return {"message": "Role deleted successfully"}


@router.get("/permissions")
def get_user_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get permissions for current user based on role"""
    
    role = db.query(UserRole).filter(UserRole.user_id == current_user.id).first()
    
    if not role:
        raise HTTPException(status_code=404, detail="User role not found")
    
    # Define permissions by role
    permissions_map = {
        RoleType.ADMIN: [
            "create_user", "read_user", "update_user", "delete_user",
            "create_product", "read_product", "update_product", "delete_product",
            "create_invoice", "read_invoice", "update_invoice", "delete_invoice",
            "view_analytics", "view_reports", "manage_subscriptions",
            "manage_roles", "view_audit_logs"
        ],
        RoleType.MANAGER: [
            "read_user", "update_user",
            "create_product", "read_product", "update_product",
            "create_invoice", "read_invoice", "update_invoice",
            "view_analytics", "view_reports"
        ],
        RoleType.STAFF: [
            "read_product",
            "create_invoice", "read_invoice",
            "view_analytics"
        ],
        RoleType.VIEWER: [
            "read_product",
            "read_invoice",
            "view_analytics"
        ]
    }
    
    permissions = permissions_map.get(role.role, [])
    
    return {
        "user_id": str(current_user.id),
        "role": role.role,
        "permissions": permissions
    }
