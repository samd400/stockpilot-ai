"""
Stock Agent — Multi-step inventory monitoring with agentic loop.
Checks stock levels, forecasts demand, calculates reorder quantities, creates alerts and POs.
"""
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from app.agents.base import AgentBase, register_agent
from app.agents.tools import TOOLS_SCHEMA


class StockAgent(AgentBase):
    name = "stock_agent"
    description = "Multi-step inventory monitoring: checks stock, forecasts demand, creates reorder alerts"
    max_iterations = 8

    def get_system_prompt(self) -> str:
        return """You are an intelligent inventory management agent for a retail business.
Your goal is to identify stock issues and take proactive action.

Follow this process:
1. Call check_inventory_health() to find low-stock products
2. For each critical product (stock=0 or very low), call calculate_reorder_quantity()
3. For products with reorder needed, create alerts using create_alert()
4. Call analyze_dead_stock() to identify items that need clearance
5. Call get_revenue_summary() to understand overall business health
6. Call finish() with a comprehensive summary

Always be specific in alert messages. Include product names, quantities, and recommended actions.
Severity levels: Critical (stock=0), High (below reorder level), Medium (getting low)."""

    def get_tools_schema(self) -> List[Dict]:
        return TOOLS_SCHEMA

    def gather_context(self, tenant_id: str, db: Session) -> Dict[str, Any]:
        from app.agents.tools import AgentTools
        tools = AgentTools(db, tenant_id)
        return {
            "tenant_id": tenant_id,
            "low_stock_preview": tools.check_inventory_health(threshold=20)[:5],
            "revenue_preview": tools.get_revenue_summary(days=7),
        }

    def build_initial_prompt(self, context: Dict[str, Any]) -> str:
        return f"""You are managing inventory for tenant {context['tenant_id']}.

Initial data snapshot:
- Low stock products (preview): {context['low_stock_preview']}
- Last 7 days revenue: {context['revenue_preview']}

Start by running a complete inventory health check and take all necessary actions.
Create specific, actionable alerts for each issue found."""


class InsightAgent(AgentBase):
    """Weekly business insight report agent."""
    name = "insight_agent"
    description = "Generates comprehensive weekly business health report"
    max_iterations = 10

    def get_system_prompt(self) -> str:
        return """You are a business intelligence agent. Your job is to generate a comprehensive
weekly business health report.

Follow this process:
1. Get revenue summary (30 days and 7 days)
2. Get top selling products
3. Analyze sales trends
4. Detect price anomalies
5. Check customer segments
6. Analyze dead stock
7. Create a single comprehensive alert with a full business health report
8. Call finish() with executive summary

Make the report actionable and specific. Include percentages, amounts, and concrete recommendations."""

    def get_tools_schema(self) -> List[Dict]:
        return TOOLS_SCHEMA

    def gather_context(self, tenant_id: str, db: Session) -> Dict[str, Any]:
        return {"tenant_id": tenant_id, "report_type": "weekly_insight"}

    def build_initial_prompt(self, context: Dict[str, Any]) -> str:
        return f"""Generate a comprehensive weekly business health report for tenant {context['tenant_id']}.
Gather all available data and create a detailed report alert."""


class ComplianceAgent(AgentBase):
    """Tax and compliance monitoring agent."""
    name = "compliance_agent"
    description = "Checks tax compliance: missing HSN codes, incorrect rates"
    max_iterations = 5

    def get_system_prompt(self) -> str:
        return """You are a tax compliance agent. Check for compliance issues and alert the business owner.
Focus on: missing HSN codes (India), missing tax codes (EU), price anomalies.
Create compliance alerts for each issue found."""

    def get_tools_schema(self) -> List[Dict]:
        return TOOLS_SCHEMA

    def gather_context(self, tenant_id: str, db: Session) -> Dict[str, Any]:
        return {"tenant_id": tenant_id}

    def build_initial_prompt(self, context: Dict[str, Any]) -> str:
        return f"""Run compliance checks for tenant {context['tenant_id']}.
Check for price anomalies and any compliance issues. Create alerts for each issue found."""


# Register all agents
register_agent(StockAgent())
register_agent(InsightAgent())
register_agent(ComplianceAgent())
