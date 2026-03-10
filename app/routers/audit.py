from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user
from app.models.user import User
from app.models.audit_log import AuditLog, AuditActionType
from typing import List, Optional
from datetime import datetime, timedelta
import json

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


def log_action(
    db: Session,
    user_id,
    action: AuditActionType,
    entity_type: str,
    entity_id: Optional[str] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Helper function to log audit actions"""
    
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=json.dumps(old_values) if old_values else None,
        new_values=json.dumps(new_values) if new_values else None,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    db.add(audit_log)
    db.commit()


@router.get("/logs")
def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    days: int = 30
):
    """Get audit logs for the current user"""
    
    query = db.query(AuditLog).filter(
        AuditLog.user_id == current_user.id
    )
    
    # Filter by date
    start_date = datetime.utcnow() - timedelta(days=days)
    query = query.filter(AuditLog.created_at >= start_date)
    
    # Filter by entity type
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    
    # Filter by action
    if action:
        query = query.filter(AuditLog.action == action)
    
    logs = query.order_by(desc(AuditLog.created_at)).limit(100).all()
    
    return [
        {
            "id": str(log.id),
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "old_values": json.loads(log.old_values) if log.old_values else None,
            "new_values": json.loads(log.new_values) if log.new_values else None,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at
        }
        for log in logs
    ]


@router.get("/logs/{entity_type}/{entity_id}")
def get_entity_audit_history(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit history for a specific entity"""
    
    logs = db.query(AuditLog).filter(
        AuditLog.user_id == current_user.id,
        AuditLog.entity_type == entity_type,
        AuditLog.entity_id == entity_id
    ).order_by(desc(AuditLog.created_at)).all()
    
    return [
        {
            "id": str(log.id),
            "action": log.action,
            "old_values": json.loads(log.old_values) if log.old_values else None,
            "new_values": json.loads(log.new_values) if log.new_values else None,
            "created_at": log.created_at
        }
        for log in logs
    ]


@router.get("/summary")
def get_audit_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = 30
):
    """Get audit summary for the current user"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    logs = db.query(AuditLog).filter(
        AuditLog.user_id == current_user.id,
        AuditLog.created_at >= start_date
    ).all()
    
    # Count by action
    action_counts = {}
    entity_counts = {}
    
    for log in logs:
        action_counts[log.action] = action_counts.get(log.action, 0) + 1
        entity_counts[log.entity_type] = entity_counts.get(log.entity_type, 0) + 1
    
    return {
        "total_actions": len(logs),
        "actions_by_type": action_counts,
        "actions_by_entity": entity_counts,
        "period_days": days
    }


@router.get("/export")
def export_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = 30
):
    """Export audit logs as JSON"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    logs = db.query(AuditLog).filter(
        AuditLog.user_id == current_user.id,
        AuditLog.created_at >= start_date
    ).order_by(desc(AuditLog.created_at)).all()
    
    export_data = [
        {
            "id": str(log.id),
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "old_values": json.loads(log.old_values) if log.old_values else None,
            "new_values": json.loads(log.new_values) if log.new_values else None,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at.isoformat()
        }
        for log in logs
    ]
    
    return {
        "export_date": datetime.utcnow().isoformat(),
        "total_records": len(export_data),
        "logs": export_data
    }
