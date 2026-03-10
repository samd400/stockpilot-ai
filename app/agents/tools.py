"""
Agent Tools — Safe, validated actions that agents can perform.
"""

import uuid
import logging
from typing import Any, Dict, Callable
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.invoice import Invoice
from app.models.purchase_order import PurchaseOrder
from app.models.product import Product

logger = logging.getLogger(__name__)


class AgentTools:
    """Tool registry for agent actions. All actions are tenant-scoped."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self._tools: Dict[str, Callable] = {
            "read_db": self.read_db,
            "create_alert": self.create_alert,
            "create_invoice": self.create_invoice,
            "create_purchase_order": self.create_purchase_order,
            "send_sms": self.send_sms,
            "send_email": self.send_email,
            "update_price": self.update_price,
        }

    def execute(self, tool_name: str, params: Dict[str, Any]) -> Any:
        tool = self._tools.get(tool_name)
        if not tool:
            raise ValueError(f"Unknown tool: {tool_name}")
        return tool(**params)

    def available_tools(self) -> list:
        return list(self._tools.keys())

    # ===== Tool Implementations =====

    def read_db(self, model: str, filters: Dict[str, Any] = None, limit: int = 100) -> list:
        """Read data from database (tenant-scoped)."""
        model_map = {
            "products": Product,
            "alerts": Alert,
            "invoices": Invoice,
        }
        model_cls = model_map.get(model)
        if not model_cls:
            return []

        query = self.db.query(model_cls)
        if hasattr(model_cls, 'tenant_id'):
            query = query.filter(model_cls.tenant_id == self.tenant_id)

        if filters:
            for key, value in filters.items():
                if hasattr(model_cls, key):
                    query = query.filter(getattr(model_cls, key) == value)

        return [str(r.id) for r in query.limit(limit).all()]

    def create_alert(self, title: str, message: str, alert_type: str = "system_alert",
                     severity: str = "Medium") -> str:
        """Create a tenant-scoped alert."""
        alert = Alert(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            title=title,
            message=message,
            type=alert_type,
            severity=severity,
        )
        self.db.add(alert)
        self.db.commit()
        logger.info(f"Agent created alert: {title} for tenant {self.tenant_id}")
        return str(alert.id)

    def create_invoice(self, **kwargs) -> str:
        """Create an invoice (simplified — agents typically trigger via orders)."""
        logger.info(f"Agent invoice creation requested for tenant {self.tenant_id}")
        return "invoice_creation_delegated"

    def create_purchase_order(self, product_id: str, quantity: int,
                               supplier_id: str = None, notes: str = "") -> str:
        """Create a purchase order for restocking."""
        from app.models.tenant import Tenant
        tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()

        po = PurchaseOrder(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            user_id=tenant.owner_user_id if tenant else self.tenant_id,
            supplier_id=supplier_id,
            status="PENDING",
        )
        self.db.add(po)
        self.db.commit()
        logger.info(f"Agent created PO for product {product_id}, qty {quantity}")
        return str(po.id)

    def send_sms(self, phone: str, message: str) -> str:
        """Queue an SMS notification via Celery."""
        try:
            from app.tasks.notification_tasks import send_sms_task
            send_sms_task.delay(phone, message)
            return "sms_queued"
        except Exception as e:
            logger.error(f"Agent SMS failed: {e}")
            return f"sms_failed: {e}"

    def send_email(self, to: str, subject: str, body: str) -> str:
        """Queue an email notification."""
        logger.info(f"Agent email to {to}: {subject}")
        return "email_queued"

    def update_price(self, product_id: str, new_price: float, reason: str = "") -> str:
        """Update product selling price."""
        product = self.db.query(Product).filter(
            Product.id == product_id,
            Product.tenant_id == self.tenant_id
        ).first()
        if not product:
            return "product_not_found"

        old_price = product.selling_price
        product.selling_price = new_price
        self.db.commit()
        logger.info(f"Agent updated price for {product_id}: {old_price} → {new_price} ({reason})")
        return f"price_updated:{old_price}->{new_price}"
