"""
Profit Agent — Analyzes profit trends, margins, and suggests pricing actions.
"""
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from app.agents.base import AgentBase, register_agent
from app.agents.tools import TOOLS_SCHEMA


class ProfitAgent(AgentBase):
    name = "profit_agent"
    description = "Analyzes profit margins, detects revenue drops, suggests pricing improvements"
    max_iterations = 8

    def get_system_prompt(self) -> str:
        return """You are a profit optimization agent for a retail business.

Follow this process:
1. Call get_revenue_summary() for last 30 days
2. Call analyze_sales_trend() to compare with previous period
3. Call detect_price_anomalies() to find low-margin products
4. Call get_top_selling_products() to understand what's driving revenue
5. For each product with margin < 10%, call create_dynamic_price_suggestion()
6. Create alerts for significant revenue drops (>15% drop = Critical)
7. Call finish() with profit health summary

Be specific: include percentage changes, revenue figures, and actionable recommendations."""

    def get_tools_schema(self) -> List[Dict]:
        return TOOLS_SCHEMA

    def gather_context(self, tenant_id: str, db: Session) -> Dict[str, Any]:
        from app.agents.tools import AgentTools
        tools = AgentTools(db, tenant_id)
        return {
            "tenant_id": tenant_id,
            "quick_revenue": tools.get_revenue_summary(days=30),
        }

    def build_initial_prompt(self, context: Dict[str, Any]) -> str:
        return f"""Analyze profit health for tenant {context['tenant_id']}.

Quick preview - last 30 days: {context['quick_revenue']}

Run full profit analysis: check trends, identify margin problems, and take action."""


class PricingAgent(AgentBase):
    name = "pricing_agent"
    description = "Optimizes product pricing based on demand, stock levels, and market conditions"
    max_iterations = 8

    def get_system_prompt(self) -> str:
        return """You are a dynamic pricing agent. Optimize product prices based on data.

Rules:
- High demand + low stock → suggest price increase (max 20%)
- Low demand + high stock → suggest price decrease (max 15%)
- Products below 10% margin → flag and suggest price increase
- Never suggest price below purchase cost + 5% margin
- Always maintain minimum 10% gross margin

Follow this process:
1. Get top selling products
2. Check inventory health
3. Analyze sales trends
4. Detect price anomalies
5. For each product needing adjustment: create_dynamic_price_suggestion()
6. Create summary alert
7. Call finish()"""

    def get_tools_schema(self) -> List[Dict]:
        return TOOLS_SCHEMA

    def gather_context(self, tenant_id: str, db: Session) -> Dict[str, Any]:
        return {"tenant_id": tenant_id}

    def build_initial_prompt(self, context: Dict[str, Any]) -> str:
        return f"""Optimize pricing for tenant {context['tenant_id']}.
Analyze demand, stock levels, and margins. Create price suggestions for products that need adjustment."""


register_agent(ProfitAgent())
register_agent(PricingAgent())
