"""Procurement Service — manages supplier POs, reorder calculations, supplier notifications."""

import uuid
import json
import logging
import requests
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.product import Product
from app.models.supplier import Supplier
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem, POStatus
from app.models.invoice_item import InvoiceItem
from app.models.invoice import Invoice
from app.models.agent_audit_log import AgentAuditLog

logger = logging.getLogger(__name__)


def calculate_reorder_quantity(db: Session, product: Product, window_days: int = 30) -> Dict:
    """Calculate optimal reorder quantity based on sales velocity."""
    cutoff = datetime.utcnow() - timedelta(days=window_days)
    total_sold = db.query(func.coalesce(func.sum(InvoiceItem.quantity), 0)).join(
        Invoice, Invoice.id == InvoiceItem.invoice_id
    ).filter(
        InvoiceItem.product_id == product.id,
        Invoice.created_at >= cutoff
    ).scalar() or 0

    avg_daily = total_sold / window_days if total_sold else 0
    lead_time = 7  # default; will be overridden by supplier lead_time_days

    reorder_point = avg_daily * lead_time
    safety_stock = avg_daily * 3  # 3-day safety buffer
    recommended_qty = max(round((avg_daily * window_days) - product.stock_quantity + safety_stock), 0)

    return {
        "product_id": str(product.id),
        "product_name": product.product_name,
        "current_stock": product.stock_quantity,
        "avg_daily_sales": round(avg_daily, 2),
        "reorder_point": round(reorder_point),
        "recommended_qty": recommended_qty,
        "needs_reorder": product.stock_quantity <= reorder_point,
    }


def find_preferred_supplier(db: Session, tenant_id: str) -> Optional[Supplier]:
    """Find the preferred supplier for a tenant."""
    return db.query(Supplier).filter(
        Supplier.tenant_id == tenant_id,
        Supplier.preferred == True
    ).first()


def create_purchase_order(
    db: Session,
    tenant_id: str,
    user_id: str,
    supplier_id: str,
    items: List[Dict],
    notes: str = "",
    currency: str = "INR",
) -> PurchaseOrder:
    """Create a purchase order with items."""
    total = 0
    po = PurchaseOrder(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        supplier_id=supplier_id,
        status=POStatus.DRAFT,
        currency=currency,
        notes=notes,
    )
    db.add(po)
    db.flush()

    for item in items:
        line_total = item["quantity"] * item["unit_cost"]
        po_item = PurchaseOrderItem(
            id=uuid.uuid4(),
            purchase_order_id=po.id,
            product_id=item["product_id"],
            quantity=item["quantity"],
            unit_cost=item["unit_cost"],
            total_price=line_total,
        )
        db.add(po_item)
        total += line_total

    po.total_amount = total

    # Set expected arrival based on supplier lead time
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if supplier and supplier.lead_time_days:
        po.expected_arrival_date = datetime.utcnow() + timedelta(days=supplier.lead_time_days)

    db.commit()
    db.refresh(po)
    return po


def send_purchase_order_to_supplier(db: Session, po: PurchaseOrder) -> bool:
    """Send PO to supplier via webhook API if configured, else mark as sent."""
    supplier = db.query(Supplier).filter(Supplier.id == po.supplier_id).first()
    if not supplier:
        return False

    if supplier.api_endpoint:
        try:
            payload = {
                "po_id": str(po.id),
                "supplier_id": str(supplier.id),
                "total_amount": po.total_amount,
                "currency": po.currency,
                "items": [
                    {"product_id": str(i.product_id), "quantity": i.quantity, "unit_cost": i.unit_cost}
                    for i in po.items
                ],
            }
            resp = requests.post(supplier.api_endpoint, json=payload, timeout=15)
            resp.raise_for_status()
            logger.info(f"PO {po.id} sent to supplier API: {supplier.api_endpoint}")
        except Exception as e:
            logger.error(f"Failed to send PO to supplier API: {e}")

    po.status = POStatus.SENT
    db.commit()
    return True


def log_agent_audit(db: Session, tenant_id: str, agent_name: str, action: str,
                    input_data: dict = None, output_data: dict = None, status: str = "success"):
    """Log an agent action to the audit trail."""
    entry = AgentAuditLog(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        agent_name=agent_name,
        action=action,
        input_data=json.dumps(input_data) if input_data else None,
        output_data=json.dumps(output_data) if output_data else None,
        status=status,
    )
    db.add(entry)
    db.commit()
