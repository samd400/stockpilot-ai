"""Agent Controller — orchestrates agent execution, status tracking, and safety."""

import logging
import json
from typing import Dict, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.agents.registry import get_agent, list_agents, _register_defaults
from app.models.tenant import Tenant
from app.services.procurement_service import log_agent_audit

logger = logging.getLogger(__name__)


class AgentController:
    """Central controller for triggering and tracking agents."""

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self._ensure_registry()

    def _ensure_registry(self):
        """Ensure agents are registered."""
        try:
            _register_defaults()
        except Exception:
            pass  # Already registered or import error

    def list_available_agents(self) -> Dict:
        """List all available agents."""
        return list_agents()

    def check_feature_flag(self, agent_name: str) -> bool:
        """Check if the tenant has the required feature flag enabled."""
        tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
        if not tenant:
            return False

        flag_map = {
            "procurement_agent": tenant.allow_auto_procurement,
            "pricing_agent": tenant.allow_dynamic_pricing,
        }
        # Default to allow_autonomous_agents for agents not in the map
        return flag_map.get(agent_name, tenant.allow_autonomous_agents)

    def trigger_agent(self, agent_name: str, params: Dict = None, dry_run: bool = True) -> Dict:
        """Trigger a specific agent with parameters."""
        agent = get_agent(agent_name)
        if not agent:
            return {"error": f"Agent '{agent_name}' not found", "available": list(list_agents().keys())}

        if not dry_run and not self.check_feature_flag(agent_name):
            log_agent_audit(self.db, self.tenant_id, agent_name, "trigger_blocked",
                            output_data={"reason": "Feature flag disabled"}, status="blocked")
            return {"error": f"Agent '{agent_name}' is disabled for this tenant"}

        try:
            handler = agent["handler"]
            result = handler(db=self.db, tenant_id=self.tenant_id, **(params or {}))

            log_agent_audit(self.db, self.tenant_id, agent_name, "triggered",
                            input_data=params, output_data=result if isinstance(result, dict) else {"result": str(result)},
                            status="success")

            return {"agent": agent_name, "status": "completed", "result": result}
        except Exception as e:
            logger.error(f"Agent {agent_name} failed: {e}")
            log_agent_audit(self.db, self.tenant_id, agent_name, "trigger_failed",
                            input_data=params, output_data={"error": str(e)}, status="failed")
            return {"agent": agent_name, "status": "failed", "error": str(e)}

    def get_agent_status(self, agent_name: str) -> Dict:
        """Get the last execution status of an agent."""
        from app.models.agent_audit_log import AgentAuditLog
        last = self.db.query(AgentAuditLog).filter(
            AgentAuditLog.tenant_id == self.tenant_id,
            AgentAuditLog.agent_name == agent_name,
        ).order_by(AgentAuditLog.created_at.desc()).first()

        if not last:
            return {"agent": agent_name, "status": "never_run"}
        return {
            "agent": agent_name,
            "last_action": last.action,
            "last_status": last.status,
            "last_run": last.created_at.isoformat() if last.created_at else None,
        }
