"""Webhook endpoint management — tenants register HTTP endpoints for events."""
import uuid
import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin, get_current_user
from app.models.webhook_log import WebhookEndpoint, WebhookDelivery

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

VALID_EVENTS = [
    "invoice.created", "invoice.paid", "invoice.cancelled",
    "payment.received", "payment.failed",
    "stock.low", "stock.out", "purchase_order.created",
    "customer.created", "rma.created",
    "*",  # all events
]


@router.get("/endpoints")
def list_endpoints(db: Session = Depends(get_db), user: Dict = Depends(require_admin)):
    endpoints = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.tenant_id == user["tenant_id"]
    ).all()
    return [_endpoint_dict(e) for e in endpoints]


@router.post("/endpoints", status_code=201)
def create_endpoint(payload: Dict[str, Any], db: Session = Depends(get_db),
                    user: Dict = Depends(require_admin)):
    events = payload.get("events", ["*"])
    invalid = [e for e in events if e not in VALID_EVENTS]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid events: {invalid}")

    endpoint = WebhookEndpoint(
        id=uuid.uuid4(),
        tenant_id=user["tenant_id"],
        url=payload["url"],
        secret=payload.get("secret"),
        events=events,
        description=payload.get("description"),
        is_active=True,
    )
    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)
    return _endpoint_dict(endpoint)


@router.patch("/endpoints/{endpoint_id}")
def update_endpoint(endpoint_id: str, payload: Dict[str, Any], db: Session = Depends(get_db),
                    user: Dict = Depends(require_admin)):
    endpoint = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.id == endpoint_id, WebhookEndpoint.tenant_id == user["tenant_id"]
    ).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    for k, v in payload.items():
        if k not in ("id", "tenant_id") and hasattr(endpoint, k):
            setattr(endpoint, k, v)
    db.commit()
    return _endpoint_dict(endpoint)


@router.delete("/endpoints/{endpoint_id}")
def delete_endpoint(endpoint_id: str, db: Session = Depends(get_db),
                    user: Dict = Depends(require_admin)):
    endpoint = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.id == endpoint_id, WebhookEndpoint.tenant_id == user["tenant_id"]
    ).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    db.delete(endpoint)
    db.commit()
    return {"message": "Endpoint deleted"}


@router.get("/endpoints/{endpoint_id}/deliveries")
def get_deliveries(endpoint_id: str, skip: int = 0, limit: int = 50,
                   db: Session = Depends(get_db), user: Dict = Depends(require_admin)):
    endpoint = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.id == endpoint_id, WebhookEndpoint.tenant_id == user["tenant_id"]
    ).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    deliveries = db.query(WebhookDelivery).filter(
        WebhookDelivery.endpoint_id == endpoint_id
    ).order_by(WebhookDelivery.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": str(d.id), "event": d.event, "status": d.status,
            "response_status": d.response_status, "duration_ms": d.duration_ms,
            "retry_count": d.retry_count, "created_at": d.created_at.isoformat(),
        }
        for d in deliveries
    ]


def _endpoint_dict(e: WebhookEndpoint) -> Dict:
    return {
        "id": str(e.id), "url": e.url, "events": e.events,
        "is_active": e.is_active, "description": e.description,
        "has_secret": bool(e.secret),
        "created_at": e.created_at.isoformat(),
    }
