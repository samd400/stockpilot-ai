"""Profit Analysis Agent — detects profit drops and suggests actions."""

import logging
from typing import List, Dict, Any
from sqlalchemy import func
from datetime import datetime, timedelta
from app.agents.base import AgentBase, AgentAction, AgentRegistry
from app.agents.tools import AgentTools
from app.models.invoice import Invoice
from app.models.product import Product
from app.services.gemini_service import ask_gemini_json

logger = logging.getLogger(__name__)


class ProfitAgent(AgentBase):
    def __init__(self):
        super().__init__("profit_agent", "Analyzes profit margins and detects drops")

    def get_llm_prompt(self, context: Dict[str, Any]) -> str:
        return f"""You are a profit analysis AI agent. Analyze the revenue data
and identify profit risks.

Revenue last 30 days: {context.get('revenue_30d', 0)}
Revenue previous 30 days: {context.get('revenue_prev_30d', 0)}
Low margin products: {context.get('low_margin_products', [])}

Decide:
1. Is there a profit drop? (severity: critical/warning/ok)
2. Which products need attention?
3. Suggested actions

Respond with JSON:
{{"profit_status": "warning", "drop_percentage": 15,
  "alerts": [{{"title": "...", "message": "...", "severity": "High"}}],
  "price_suggestions": [{{"product_id": "...", "suggested_price": 100, "reason": "..."}}]
}}"""

    def analyze(self, tenant_id: str, db_session, tools: AgentTools) -> List[AgentAction]:
        actions = []
        now = datetime.utcnow()
        d30_ago = now - timedelta(days=30)
        d60_ago = now - timedelta(days=60)

        # Revenue last 30 days
        rev_30 = db_session.query(func.sum(Invoice.total_amount)).filter(
            Invoice.tenant_id == tenant_id,
            Invoice.created_at >= d30_ago
        ).scalar() or 0

        # Revenue previous 30 days
        rev_prev = db_session.query(func.sum(Invoice.total_amount)).filter(
            Invoice.tenant_id == tenant_id,
            Invoice.created_at >= d60_ago,
            Invoice.created_at < d30_ago
        ).scalar() or 0

        # Low margin products (margin < 15%)
        low_margin = db_session.query(Product).filter(
            Product.tenant_id == tenant_id,
            Product.selling_price > 0,
            Product.purchase_price > 0,
        ).all()

        low_margin_data = []
        for p in low_margin:
            margin = ((p.selling_price - p.purchase_price) / p.selling_price) * 100
            if margin < 15:
                low_margin_data.append({
                    "id": str(p.id), "name": p.product_name,
                    "cost": p.purchase_price, "price": p.selling_price,
                    "margin_pct": round(margin, 1)
                })

        context = {
            "revenue_30d": rev_30,
            "revenue_prev_30d": rev_prev,
            "low_margin_products": low_margin_data[:20],
        }

        decisions = ask_gemini_json(self.get_llm_prompt(context))

        if decisions:
            for alert_data in decisions.get("alerts", []):
                actions.append(AgentAction(
                    tool_name="create_alert",
                    params={
                        "title": alert_data.get("title", "Profit Alert"),
                        "message": alert_data.get("message", "Profit analysis detected an issue."),
                        "alert_type": "profit_alert",
                        "severity": alert_data.get("severity", "Medium"),
                    },
                    reason="Profit analysis by agent",
                ))
        else:
            # Fallback logic
            if rev_prev > 0 and rev_30 < rev_prev * 0.85:
                drop_pct = round((1 - rev_30 / rev_prev) * 100, 1)
                actions.append(AgentAction(
                    tool_name="create_alert",
                    params={
                        "title": f"Revenue Drop: {drop_pct}%",
                        "message": f"Revenue dropped {drop_pct}% compared to previous period. "
                                   f"Current: {rev_30:.0f}, Previous: {rev_prev:.0f}",
                        "alert_type": "profit_alert",
                        "severity": "Critical" if drop_pct > 30 else "High",
                    },
                    reason=f"Revenue dropped {drop_pct}%",
                ))

        return actions


profit_agent = ProfitAgent()
AgentRegistry.register(profit_agent)
