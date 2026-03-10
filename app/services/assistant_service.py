"""Assistant Service — Gemini-powered conversational business assistant with schema validation."""

import json
import logging
from typing import Dict, Optional, Any
from sqlalchemy.orm import Session

from app.services.gemini_service import ask_gemini_json, call_gemini
from app.services.procurement_service import create_purchase_order, log_agent_audit
from app.models.product import Product
from app.models.supplier import Supplier
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)

# Valid actions the assistant can execute
ALLOWED_ACTIONS = {
    "create_purchase_order",
    "update_price",
    "create_alert",
    "get_stock_status",
    "get_sales_summary",
    "reorder_analysis",
}

ACTION_SCHEMAS = {
    "create_purchase_order": {
        "required": ["supplier_id", "items"],
        "items_fields": ["product_id", "quantity", "unit_cost"],
    },
    "update_price": {
        "required": ["product_id", "new_price"],
    },
    "create_alert": {
        "required": ["message", "severity"],
    },
    "get_stock_status": {
        "required": ["product_id"],
    },
    "get_sales_summary": {
        "required": [],
    },
    "reorder_analysis": {
        "required": [],
    },
}


def validate_action_schema(action: str, params: Dict) -> Dict:
    """Validate that Gemini's response matches expected schema for the action."""
    if action not in ALLOWED_ACTIONS:
        return {"valid": False, "error": f"Unknown action: {action}. Allowed: {list(ALLOWED_ACTIONS)}"}

    schema = ACTION_SCHEMAS.get(action, {})
    missing = [f for f in schema.get("required", []) if f not in params]
    if missing:
        return {"valid": False, "error": f"Missing required fields: {missing}"}

    return {"valid": True}


async def process_query(db: Session, tenant_id: str, query: str) -> Dict:
    """
    Process a natural language query via Gemini and return structured response.
    Does NOT execute — just analyzes and returns proposed action.
    """
    system_prompt = f"""You are StockPilot, an AI business assistant for inventory management.
The user is a business owner. Tenant ID: {tenant_id}.

Based on the user's query, determine what action to take.
You MUST respond with ONLY valid JSON (no markdown, no explanation) in this format:
{{
    "action": "<one of: {', '.join(ALLOWED_ACTIONS)}>",
    "params": {{ ... action-specific parameters ... }},
    "explanation": "Brief explanation of what will happen"
}}

If the query is just a question requiring information (not an action), respond:
{{
    "action": "none",
    "params": {{}},
    "explanation": "Your answer to their question"
}}
"""

    try:
        result = await ask_gemini_json(f"{system_prompt}\n\nUser query: {query}")
        if not result:
            return {
                "action": "none",
                "params": {},
                "explanation": "I couldn't process that query. Please try rephrasing."
            }

        action = result.get("action", "none")
        params = result.get("params", {})
        explanation = result.get("explanation", "")

        # Validate
        if action != "none":
            validation = validate_action_schema(action, params)
            if not validation["valid"]:
                return {
                    "action": action,
                    "params": params,
                    "explanation": explanation,
                    "validation_error": validation["error"],
                    "executable": False,
                }

        log_agent_audit(db, tenant_id, "assistant", "query",
                        input_data={"query": query},
                        output_data=result, status="success")

        return {
            "action": action,
            "params": params,
            "explanation": explanation,
            "executable": action != "none",
        }
    except Exception as e:
        logger.error(f"Assistant query failed: {e}")
        return {"action": "none", "params": {}, "explanation": f"Error processing query: {str(e)}"}


async def execute_action(db: Session, tenant_id: str, user_id: str, action: str, params: Dict) -> Dict:
    """Execute a validated action from the assistant."""
    # Safety: re-validate
    validation = validate_action_schema(action, params)
    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}

    # Check tenant feature flags
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return {"success": False, "error": "Tenant not found"}

    if not tenant.allow_autonomous_agents:
        log_agent_audit(db, tenant_id, "assistant", f"execute_{action}",
                        output_data={"error": "Autonomous agents disabled"}, status="blocked")
        return {"success": False, "error": "Autonomous agents are disabled for your account"}

    try:
        result = _dispatch_action(db, tenant_id, user_id, action, params)
        log_agent_audit(db, tenant_id, "assistant", f"execute_{action}",
                        input_data=params, output_data=result, status="success")
        return {"success": True, "result": result}
    except Exception as e:
        log_agent_audit(db, tenant_id, "assistant", f"execute_{action}",
                        input_data=params, output_data={"error": str(e)}, status="failed")
        return {"success": False, "error": str(e)}


def _dispatch_action(db: Session, tenant_id: str, user_id: str, action: str, params: Dict) -> Any:
    """Route action to the appropriate service function."""
    if action == "create_purchase_order":
        supplier_id = params["supplier_id"]
        items = params["items"]
        po = create_purchase_order(
            db=db, tenant_id=tenant_id, user_id=user_id,
            supplier_id=supplier_id, items=items,
        )
        return {"po_id": str(po.id), "status": po.status.value if hasattr(po.status, 'value') else po.status}

    elif action == "update_price":
        product = db.query(Product).filter(
            Product.id == params["product_id"], Product.tenant_id == tenant_id
        ).first()
        if not product:
            raise ValueError("Product not found")
        product.selling_price = params["new_price"]
        db.commit()
        return {"product_id": str(product.id), "new_price": params["new_price"]}

    elif action == "create_alert":
        from app.models.alert import Alert
        import uuid
        alert = Alert(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            message=params["message"],
            severity=params.get("severity", "MEDIUM"),
        )
        db.add(alert)
        db.commit()
        return {"alert_id": str(alert.id)}

    elif action == "get_stock_status":
        product = db.query(Product).filter(
            Product.id == params["product_id"], Product.tenant_id == tenant_id
        ).first()
        if not product:
            raise ValueError("Product not found")
        return {
            "product_name": product.product_name,
            "stock_quantity": product.stock_quantity,
            "selling_price": product.selling_price,
        }

    elif action == "get_sales_summary":
        from sqlalchemy import func
        from app.models.invoice import Invoice
        total = db.query(func.sum(Invoice.total_amount)).filter(Invoice.tenant_id == tenant_id).scalar() or 0
        count = db.query(func.count(Invoice.id)).filter(Invoice.tenant_id == tenant_id).scalar() or 0
        return {"total_revenue": total, "invoice_count": count}

    elif action == "reorder_analysis":
        from app.services.procurement_service import calculate_reorder_quantity
        products = db.query(Product).filter(Product.tenant_id == tenant_id).all()
        analyses = [calculate_reorder_quantity(db, p) for p in products]
        return {"products_analyzed": len(analyses), "needs_reorder": [a for a in analyses if a["needs_reorder"]]}

    raise ValueError(f"Unknown action: {action}")
