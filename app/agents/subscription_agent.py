"""Subscription Agent — auto-downgrades expired subscriptions."""

import logging
from typing import List, Dict, Any
from datetime import datetime
from app.agents.base import AgentBase, AgentAction, AgentRegistry
from app.agents.tools import AgentTools
from app.models.tenant import Tenant
from app.models.subscription_plan import SubscriptionPlan

logger = logging.getLogger(__name__)


class SubscriptionAgent(AgentBase):
    def __init__(self):
        super().__init__("subscription_agent", "Auto-downgrades expired subscriptions")

    def get_llm_prompt(self, context: Dict[str, Any]) -> str:
        return ""  # No LLM needed — rule-based

    def analyze(self, tenant_id: str, db_session, tools: AgentTools) -> List[AgentAction]:
        """Check if THIS tenant's subscription is expired and alert."""
        actions = []

        tenant = db_session.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            return actions

        if tenant.subscription_expiry and tenant.subscription_expiry < datetime.utcnow():
            # Find free plan
            free_plan = db_session.query(SubscriptionPlan).filter(
                SubscriptionPlan.name == "Free"
            ).first()

            if free_plan and str(tenant.subscription_plan_id) != str(free_plan.id):
                tenant.subscription_plan_id = free_plan.id
                db_session.commit()

                actions.append(AgentAction(
                    tool_name="create_alert",
                    params={
                        "title": "Subscription Expired — Downgraded",
                        "message": f"Your subscription expired on {tenant.subscription_expiry.strftime('%Y-%m-%d')}. "
                                   f"Account has been downgraded to Free plan. Upgrade to restore features.",
                        "alert_type": "subscription_alert",
                        "severity": "Critical",
                    },
                    reason="Subscription expired, auto-downgraded",
                ))
            else:
                actions.append(AgentAction(
                    tool_name="create_alert",
                    params={
                        "title": "Subscription Expiry Warning",
                        "message": f"Your subscription expired on {tenant.subscription_expiry.strftime('%Y-%m-%d')}. "
                                   f"Please renew to continue using all features.",
                        "alert_type": "subscription_alert",
                        "severity": "High",
                    },
                    reason="Subscription expired",
                ))

        return actions


subscription_agent = SubscriptionAgent()
AgentRegistry.register(subscription_agent)
