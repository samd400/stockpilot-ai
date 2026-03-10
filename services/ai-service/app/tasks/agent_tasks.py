"""
Celery periodic tasks — run agents for all tenants on schedule.
"""
import logging
from celery import Celery
import os

logger = logging.getLogger(__name__)

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
celery_app = Celery("ai-service", broker=CELERY_BROKER_URL, backend=CELERY_BROKER_URL)

celery_app.conf.beat_schedule = {
    "stock-agent-every-4h": {
        "task": "app.tasks.agent_tasks.run_stock_agent_periodic",
        "schedule": 14400,  # 4 hours
    },
    "profit-agent-daily": {
        "task": "app.tasks.agent_tasks.run_profit_agent_periodic",
        "schedule": 86400,  # 24 hours
    },
    "pricing-agent-daily": {
        "task": "app.tasks.agent_tasks.run_pricing_agent_periodic",
        "schedule": 86400,
    },
    "insight-agent-weekly": {
        "task": "app.tasks.agent_tasks.run_insight_agent_periodic",
        "schedule": 604800,  # 7 days
    },
    "compliance-agent-weekly": {
        "task": "app.tasks.agent_tasks.run_compliance_agent_periodic",
        "schedule": 604800,
    },
}


def _run_for_all_tenants(agent_name: str, dry_run: bool = False):
    """Run agent for all active tenants."""
    from app.core.database import SessionLocal
    from sqlalchemy import text
    from app.agents.base import get_agent
    from app.agents.tools import AgentTools

    db = SessionLocal()
    results = []
    try:
        tenants = db.execute(
            text("SELECT id FROM tenants WHERE is_active = true")
        ).fetchall()
        agent = get_agent(agent_name)
        if not agent:
            logger.error(f"Agent {agent_name} not found in registry")
            return [{"error": f"Agent {agent_name} not found"}]

        for tenant_row in tenants:
            tenant_id = str(tenant_row[0])
            try:
                tools = AgentTools(db, tenant_id)
                result = agent.run(tenant_id, db, tools, dry_run=dry_run)
                results.append({
                    "tenant_id": tenant_id,
                    "status": result.status,
                    "actions": result.actions_executed,
                    "errors": len(result.errors),
                })
                logger.info(f"Agent {agent_name} for tenant {tenant_id}: "
                            f"{result.status}, {result.actions_executed} actions")
            except Exception as e:
                logger.error(f"Agent {agent_name} failed for tenant {tenant_id}: {e}")
                results.append({"tenant_id": tenant_id, "error": str(e)})
    finally:
        db.close()
    return results


@celery_app.task(name="app.tasks.agent_tasks.run_stock_agent_periodic")
def run_stock_agent_periodic():
    # Import agents to register them
    import app.agents.stock_agent  # noqa
    return _run_for_all_tenants("stock_agent")


@celery_app.task(name="app.tasks.agent_tasks.run_profit_agent_periodic")
def run_profit_agent_periodic():
    import app.agents.profit_agent  # noqa
    return _run_for_all_tenants("profit_agent")


@celery_app.task(name="app.tasks.agent_tasks.run_pricing_agent_periodic")
def run_pricing_agent_periodic():
    import app.agents.profit_agent  # noqa (pricing agent registered here)
    return _run_for_all_tenants("pricing_agent")


@celery_app.task(name="app.tasks.agent_tasks.run_insight_agent_periodic")
def run_insight_agent_periodic():
    import app.agents.stock_agent  # noqa (insight agent registered here)
    return _run_for_all_tenants("insight_agent")


@celery_app.task(name="app.tasks.agent_tasks.run_compliance_agent_periodic")
def run_compliance_agent_periodic():
    import app.agents.stock_agent  # noqa (compliance agent registered here)
    return _run_for_all_tenants("compliance_agent")
