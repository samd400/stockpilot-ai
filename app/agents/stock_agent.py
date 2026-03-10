"""Stock Monitoring Agent — detects low stock and triggers auto-reorder."""

import logging
from typing import List, Dict, Any
from app.agents.base import AgentBase, AgentAction, AgentRegistry
from app.agents.tools import AgentTools
from app.models.product import Product
from app.services.gemini_service import ask_gemini_json

logger = logging.getLogger(__name__)

REORDER_THRESHOLD = 10  # Default reorder point


class StockAgent(AgentBase):
    def __init__(self):
        super().__init__("stock_agent", "Monitors stock levels and triggers auto-reorder")

    def get_llm_prompt(self, context: Dict[str, Any]) -> str:
        return f"""You are a stock management AI agent. Analyze the following products
and decide which ones need reordering.

Products with low stock:
{context.get('low_stock_products', '[]')}

For each product, decide:
1. Should we reorder? (yes/no)
2. Recommended reorder quantity
3. Urgency (critical/high/medium/low)

Respond with JSON:
{{"decisions": [
  {{"product_id": "...", "reorder": true, "quantity": 50, "urgency": "high", "reason": "..."}}
]}}"""

    def analyze(self, tenant_id: str, db_session, tools: AgentTools) -> List[AgentAction]:
        actions = []

        # Find products with low stock
        low_stock = db_session.query(Product).filter(
            Product.tenant_id == tenant_id,
            Product.stock_quantity <= REORDER_THRESHOLD,
            Product.stock_quantity >= 0
        ).all()

        if not low_stock:
            return actions

        # Prepare context for LLM
        product_data = [
            {"id": str(p.id), "name": p.product_name, "stock": p.stock_quantity,
             "selling_price": p.selling_price, "type": p.product_type}
            for p in low_stock
        ]

        # Ask Gemini for decisions
        decisions = ask_gemini_json(self.get_llm_prompt({"low_stock_products": product_data}))

        if decisions and "decisions" in decisions:
            for d in decisions["decisions"]:
                if d.get("reorder"):
                    # Create alert
                    actions.append(AgentAction(
                        tool_name="create_alert",
                        params={
                            "title": f"Low Stock: {d.get('reason', 'Auto-detected')}",
                            "message": f"Product stock is low. Recommended reorder: {d.get('quantity', 50)} units.",
                            "alert_type": "stock_alert",
                            "severity": "High" if d.get("urgency") == "critical" else "Medium",
                        },
                        reason=d.get("reason", "Low stock detected by agent"),
                    ))
        else:
            # Fallback: create alerts without LLM
            for p in low_stock:
                actions.append(AgentAction(
                    tool_name="create_alert",
                    params={
                        "title": f"Low Stock: {p.product_name}",
                        "message": f"{p.product_name} has only {p.stock_quantity} units left. Consider reordering.",
                        "alert_type": "stock_alert",
                        "severity": "Critical" if p.stock_quantity == 0 else "High",
                    },
                    reason=f"Stock at {p.stock_quantity} units",
                ))

        return actions


# Register
stock_agent = StockAgent()
AgentRegistry.register(stock_agent)
