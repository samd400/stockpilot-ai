"""Agent Registry — central registry of all agents available in the system."""

from typing import Dict, Callable, Any

_AGENT_REGISTRY: Dict[str, Dict[str, Any]] = {}


def register_agent(name: str, handler: Callable, description: str = "", category: str = "general"):
    """Register an agent with the orchestrator."""
    _AGENT_REGISTRY[name] = {
        "name": name,
        "handler": handler,
        "description": description,
        "category": category,
    }


def get_agent(name: str) -> Dict:
    """Get a registered agent by name."""
    return _AGENT_REGISTRY.get(name)


def list_agents() -> Dict:
    """List all registered agents."""
    return {name: {"description": a["description"], "category": a["category"]} for name, a in _AGENT_REGISTRY.items()}


# Register built-in agents on import
def _register_defaults():
    from app.services.procurement_agent import run_procurement_agent
    from app.services.pricing_agent import get_recommendations as pricing_recommendations
    from app.ml.forecast import predict_demand

    register_agent(
        "procurement_agent",
        run_procurement_agent,
        "Autonomous procurement — identifies low stock and creates purchase orders",
        category="procurement",
    )
    register_agent(
        "pricing_agent",
        pricing_recommendations,
        "Dynamic pricing — analyzes demand and stock to recommend prices",
        category="pricing",
    )
    register_agent(
        "forecast_agent",
        predict_demand,
        "Demand forecasting — predicts future sales using linear regression",
        category="analytics",
    )
