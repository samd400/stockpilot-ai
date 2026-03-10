"""
Celery tasks for running agents periodically.
"""

from app.core.celery_config import celery_app
from app.core.database import SessionLocal
from app.models.tenant import Tenant
from app.agents.base import AgentExecutor, AgentRegistry
from app.agents.tools import AgentTools
import logging

# Import agents to register them
from app.agents import stock_agent, profit_agent, pricing_agent, subscription_agent, sync_agent

logger = logging.getLogger(__name__)


def _run_agent_for_all_tenants(agent_name: str):
    """Run a specific agent for all active tenants."""
    db = SessionLocal()
    try:
        tenants = db.query(Tenant).filter(Tenant.is_active == True).all()
        results = []
        for tenant in tenants:
            tools = AgentTools(db, str(tenant.id))
            executor = AgentExecutor(db, tools)
            result = executor.run_agent(agent_name, str(tenant.id))
            results.append({
                "tenant_id": str(tenant.id),
                "actions_proposed": result.actions_proposed,
                "actions_executed": result.actions_executed,
                "errors": result.errors,
            })
        return results
    except Exception as e:
        logger.error(f"Agent task {agent_name} failed: {e}")
        return [{"error": str(e)}]
    finally:
        db.close()


@celery_app.task(name="app.tasks.agent_tasks.run_stock_agent")
def run_stock_agent():
    """Run stock monitoring agent for all tenants."""
    return _run_agent_for_all_tenants("stock_agent")


@celery_app.task(name="app.tasks.agent_tasks.run_profit_agent")
def run_profit_agent():
    """Run profit analysis agent for all tenants."""
    return _run_agent_for_all_tenants("profit_agent")


@celery_app.task(name="app.tasks.agent_tasks.run_pricing_agent")
def run_pricing_agent():
    """Run pricing suggestion agent for all tenants."""
    return _run_agent_for_all_tenants("pricing_agent")


@celery_app.task(name="app.tasks.agent_tasks.run_subscription_agent")
def run_subscription_agent():
    """Run subscription auto-downgrade agent for all tenants."""
    return _run_agent_for_all_tenants("subscription_agent")


@celery_app.task(name="app.tasks.agent_tasks.run_sync_agent")
def run_sync_agent():
    """Run storefront sync agent for all tenants."""
    return _run_agent_for_all_tenants("sync_agent")


@celery_app.task(name="app.tasks.agent_tasks.run_all_agents")
def run_all_agents():
    """Run all agents for all tenants."""
    db = SessionLocal()
    try:
        tenants = db.query(Tenant).filter(Tenant.is_active == True).all()
        all_results = []
        for tenant in tenants:
            tools = AgentTools(db, str(tenant.id))
            executor = AgentExecutor(db, tools)
            results = executor.run_all(str(tenant.id))
            for r in results:
                all_results.append({
                    "tenant_id": str(tenant.id),
                    "agent": r.agent_name,
                    "proposed": r.actions_proposed,
                    "executed": r.actions_executed,
                })
        return all_results
    except Exception as e:
        logger.error(f"Run all agents failed: {e}")
        return [{"error": str(e)}]
    finally:
        db.close()
