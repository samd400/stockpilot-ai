"""Connector Webhooks Router — handles incoming webhooks from external channels."""

from fastapi import APIRouter, Request, HTTPException
from typing import Dict

from app.connectors.mock_connector import MockConnector

router = APIRouter(prefix="/webhooks/connectors", tags=["Connectors"])

# Registry of available connectors
CONNECTORS = {
    "mock": MockConnector,
}


@router.post("/{connector_name}")
async def connector_webhook(connector_name: str, request: Request):
    """Receive webhook from an external sales channel connector."""
    connector_class = CONNECTORS.get(connector_name)
    if not connector_class:
        raise HTTPException(status_code=404, detail=f"Unknown connector: {connector_name}")

    body = await request.json()
    tenant_id = body.get("tenant_id", "unknown")

    connector = connector_class(tenant_id=tenant_id)

    action = body.get("action", "")
    if action == "fetch_orders":
        orders = connector.fetch_orders()
        return {"connector": connector_name, "orders": orders}
    elif action == "push_inventory":
        result = connector.push_inventory_update(body.get("product_id", ""), body.get("quantity", 0))
        return {"connector": connector_name, "result": result}
    elif action == "health_check":
        return connector.health_check()
    else:
        return {"connector": connector_name, "message": "Webhook received", "body": body}
