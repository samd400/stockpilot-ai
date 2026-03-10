"""
Alerts router — CRUD for business alerts + AI-driven alert generation.
"""
import uuid
import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.alert import Alert

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/")
def list_alerts(
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user),
):
    """List alerts for the current tenant."""
    q = db.query(Alert).filter(Alert.tenant_id == user["tenant_id"])
    if unread_only:
        q = q.filter(Alert.is_read == False)
    alerts = q.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": str(a.id),
            "title": a.title,
            "message": a.message,
            "type": a.type,
            "severity": a.severity,
            "is_read": a.is_read,
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "created_at": a.created_at.isoformat(),
        }
        for a in alerts
    ]


@router.post("/generate")
def generate_alerts(db: Session = Depends(get_db), user: Dict = Depends(get_current_user)):
    """
    Generate AI-driven alerts based on current business state.
    Checks low stock, overdue invoices, and other conditions.
    """
    import os
    import httpx

    tenant_id = user["tenant_id"]
    generated = []

    # Check for low stock via inventory-service
    try:
        inventory_url = os.getenv("INVENTORY_SERVICE_URL", "http://inventory-service:8002")
        service_token = os.getenv("SERVICE_TOKEN", "")
        resp = httpx.get(
            f"{inventory_url}/products",
            params={"tenant_id": tenant_id, "limit": 500},
            headers={"X-Service-Token": service_token},
            timeout=5.0
        )
        if resp.status_code == 200:
            data = resp.json()
            products = data.get("products", data) if isinstance(data, dict) else data
            if isinstance(products, list):
                for p in products:
                    stock = p.get("stock_quantity", 0) or 0
                    reorder = p.get("reorder_level", 10) or 10
                    if stock <= reorder and stock >= 0:
                        # Check if alert already exists recently
                        existing = db.query(Alert).filter(
                            Alert.tenant_id == tenant_id,
                            Alert.entity_id == str(p["id"]),
                            Alert.type == "low_stock",
                            Alert.is_read == False,
                        ).first()
                        if not existing:
                            alert = Alert(
                                id=uuid.uuid4(),
                                tenant_id=tenant_id,
                                title=f"Low Stock: {p['product_name']}",
                                message=f"Stock for '{p['product_name']}' is {stock} units "
                                        f"(reorder level: {reorder}). Please restock soon.",
                                type="low_stock",
                                severity="High" if stock == 0 else "Medium",
                                entity_type="product",
                                entity_id=str(p["id"]),
                            )
                            db.add(alert)
                            generated.append({"type": "low_stock", "product": p["product_name"]})
    except Exception as e:
        logger.warning(f"Could not check inventory for alerts: {e}")

    # Check for overdue invoices
    try:
        from sqlalchemy import text
        overdue_rows = db.execute(
            text("""SELECT id, invoice_number, customer_name, total_amount, due_date
                    FROM invoices
                    WHERE tenant_id = :tid
                    AND status NOT IN ('paid', 'PAID', 'cancelled', 'CANCELLED')
                    AND due_date < NOW()
                    LIMIT 20"""),
            {"tid": tenant_id}
        ).fetchall()

        for row in overdue_rows:
            existing = db.query(Alert).filter(
                Alert.tenant_id == tenant_id,
                Alert.entity_id == str(row[0]),
                Alert.type == "overdue_invoice",
                Alert.is_read == False,
            ).first()
            if not existing:
                alert = Alert(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    title=f"Overdue Invoice: {row[1]}",
                    message=f"Invoice {row[1]} for {row[2]} (₹{row[3]:,.2f}) is overdue since {row[4]}.",
                    type="overdue_invoice",
                    severity="High",
                    entity_type="invoice",
                    entity_id=str(row[0]),
                )
                db.add(alert)
                generated.append({"type": "overdue_invoice", "invoice": row[1]})
    except Exception as e:
        logger.warning(f"Could not check invoices for alerts: {e}")

    db.commit()
    return {
        "generated": len(generated),
        "alerts": generated,
        "message": f"Generated {len(generated)} new alerts.",
    }


@router.patch("/{alert_id}/read")
def mark_alert_read(
    alert_id: str,
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user),
):
    """Mark a specific alert as read."""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.tenant_id == user["tenant_id"],
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = True
    db.commit()
    return {"id": str(alert.id), "is_read": True}


@router.post("/mark-all-read")
def mark_all_alerts_read(
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user),
):
    """Mark all unread alerts for this tenant as read."""
    count = db.query(Alert).filter(
        Alert.tenant_id == user["tenant_id"],
        Alert.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"marked_read": count, "message": f"Marked {count} alerts as read."}


@router.delete("/{alert_id}")
def delete_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    user: Dict = Depends(get_current_user),
):
    """Delete an alert."""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.tenant_id == user["tenant_id"],
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(alert)
    db.commit()
    return {"deleted": True}
