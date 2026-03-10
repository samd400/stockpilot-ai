from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user
from app.models.alert import Alert
from app.services.alert_service import generate_smart_alerts

router = APIRouter(prefix="/alerts", tags=["Alerts"])


# ======================================
# GENERATE SMART ALERTS
# ======================================
@router.post("/generate")
def generate_alerts(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    generate_smart_alerts(db, current_user.id)
    return {"message": "Smart alerts generated"}


# ======================================
# GET ALL ALERTS
# ======================================
@router.get("/")
def get_alerts(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    alerts = db.query(Alert).filter(
        Alert.user_id == current_user.id
    ).order_by(Alert.created_at.desc()).all()

    return alerts


# ======================================
# MARK ALERT AS READ
# ======================================
@router.patch("/{alert_id}/read")
def mark_alert_read(
    alert_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_read = True
    db.commit()

    return {"message": "Alert marked as read"}
