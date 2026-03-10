"""Procurement Celery tasks — periodic autonomous procurement for all tenants."""

import logging
from app.core.celery_config import celery_app
from app.core.database import SessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from app.services.procurement_agent import run_procurement_agent

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.procurement_tasks.run_procurement_for_tenant")
def run_procurement_for_tenant(tenant_id: str, dry_run: bool = False):
    """Run procurement agent for a single tenant."""
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.tenant_id == tenant_id, User.role == "admin").first()
        if not admin:
            logger.warning(f"No admin found for tenant {tenant_id}")
            return {"error": "No admin user found"}
        result = run_procurement_agent(db, tenant_id=tenant_id, user_id=str(admin.id), dry_run=dry_run)
        return result
    except Exception as e:
        logger.error(f"Procurement agent failed for tenant {tenant_id}: {e}")
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.procurement_tasks.run_procurement_for_all_tenants")
def run_procurement_for_all_tenants():
    """Periodic task: run procurement agent for every active tenant."""
    db = SessionLocal()
    try:
        tenants = db.query(Tenant).filter(Tenant.is_active == True).all()
        results = {}
        for tenant in tenants:
            r = run_procurement_for_tenant.delay(str(tenant.id), dry_run=False)
            results[str(tenant.id)] = "dispatched"
        return results
    finally:
        db.close()
