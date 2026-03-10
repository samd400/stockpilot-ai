from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.tenant import Tenant
from app.models.user import User, UserRoleEnum
from app.models.audit_log import AuditLog
from app.routers.auth import get_current_user
from app.schemas.auth import TenantResponse, TenantUpdateRequest

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.get("/me", response_model=TenantResponse)
def get_tenant(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id,
                                      Tenant.is_active == True).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.patch("/me", response_model=TenantResponse)
def update_tenant(payload: TenantUpdateRequest, request: Request,
                  current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRoleEnum.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id,
                                      Tenant.is_active == True).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(tenant, k, v)
    db.add(AuditLog(tenant_id=current_user.tenant_id, user_id=current_user.id,
                    action="UPDATE_PROFILE", ip_address=request.client.host if request.client else None,
                    details={"fields": list(update_data.keys())}))
    db.commit()
    db.refresh(tenant)
    return tenant
