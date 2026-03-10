"""Sync Agent — syncs storefront data when products change."""

import logging
from typing import List, Dict, Any
from app.agents.base import AgentBase, AgentAction, AgentRegistry
from app.agents.tools import AgentTools

logger = logging.getLogger(__name__)


class SyncAgent(AgentBase):
    def __init__(self):
        super().__init__("sync_agent", "Syncs storefront product catalog")

    def get_llm_prompt(self, context: Dict[str, Any]) -> str:
        return ""  # Rule-based sync

    def analyze(self, tenant_id: str, db_session, tools: AgentTools) -> List[AgentAction]:
        """Placeholder: In production, this would push product updates to the storefront CDN/cache."""
        actions = []

        # In production: invalidate storefront cache, trigger rebuild, etc.
        logger.info(f"Sync agent running for tenant {tenant_id} — storefront sync check")

        return actions


sync_agent = SyncAgent()
AgentRegistry.register(sync_agent)
