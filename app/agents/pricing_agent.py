"""Pricing Agent — suggests dynamic pricing adjustments."""

import logging
from typing import List, Dict, Any
from sqlalchemy import func
from datetime import datetime, timedelta
from app.agents.base import AgentBase, AgentAction, AgentRegistry
from app.agents.tools import AgentTools
from app.models.product import Product
from app.models.invoice_item import InvoiceItem
from app.models.invoice import Invoice
from app.services.gemini_service import ask_gemini_json

logger = logging.getLogger(__name__)


class PricingAgent(AgentBase):
    def __init__(self):
        super().__init__("pricing_agent", "Suggests dynamic pricing based on demand and stock")

    def get_llm_prompt(self, context: Dict[str, Any]) -> str:
        return f"""You are a pricing optimization AI agent.
Analyze product sales and stock data to suggest price adjustments.

Products data:
{context.get('products', [])}

Rules:
- High demand + low stock → increase price (max 20%)
- Low demand + high stock → decrease price (max 15%)
- Healthy margin must be maintained (>10%)

Respond with JSON:
{{"suggestions": [
  {{"product_id": "...", "current_price": 100, "suggested_price": 110, "reason": "..."}}
]}}"""

    def analyze(self, tenant_id: str, db_session, tools: AgentTools) -> List[AgentAction]:
        actions = []
        d30_ago = datetime.utcnow() - timedelta(days=30)

        products = db_session.query(Product).filter(
            Product.tenant_id == tenant_id
        ).limit(50).all()

        product_data = []
        for p in products:
            sold_qty = db_session.query(func.sum(InvoiceItem.quantity)).join(
                Invoice, Invoice.id == InvoiceItem.invoice_id
            ).filter(
                InvoiceItem.product_id == p.id,
                Invoice.created_at >= d30_ago
            ).scalar() or 0

            product_data.append({
                "id": str(p.id), "name": p.product_name,
                "cost": p.purchase_price, "price": p.selling_price,
                "stock": p.stock_quantity, "sold_30d": sold_qty
            })

        if not product_data:
            return actions

        decisions = ask_gemini_json(self.get_llm_prompt({"products": product_data}))

        if decisions:
            for s in decisions.get("suggestions", []):
                if s.get("suggested_price") and s["suggested_price"] != s.get("current_price"):
                    actions.append(AgentAction(
                        tool_name="create_alert",
                        params={
                            "title": f"Price Suggestion: {s.get('reason', 'Pricing optimization')}",
                            "message": f"Suggested price change: {s.get('current_price')} → {s['suggested_price']}. "
                                       f"Reason: {s.get('reason', '')}",
                            "alert_type": "system_alert",
                            "severity": "Low",
                        },
                        reason=s.get("reason", "Dynamic pricing suggestion"),
                    ))

        return actions


pricing_agent = PricingAgent()
AgentRegistry.register(pricing_agent)
