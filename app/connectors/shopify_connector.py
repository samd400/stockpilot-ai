"""
Shopify Connector — syncs orders and inventory via Shopify REST Admin API.
Config keys: shop_domain, access_token
"""
import logging
from typing import List, Dict, Optional

import httpx

from app.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)

SHOPIFY_API_VERSION = "2024-01"


class ShopifyConnector(BaseConnector):
    """
    Production Shopify connector.
    Requires: config["shop_domain"], config["access_token"]
    """

    def get_channel_name(self) -> str:
        return "shopify"

    def _base_url(self) -> str:
        domain = self.config["shop_domain"].rstrip("/")
        return f"https://{domain}/admin/api/{SHOPIFY_API_VERSION}"

    def _headers(self) -> Dict:
        return {
            "X-Shopify-Access-Token": self.config["access_token"],
            "Content-Type": "application/json",
        }

    def fetch_orders(self, since: Optional[str] = None) -> List[Dict]:
        """Fetch unfulfilled orders from Shopify."""
        params = {"status": "open", "limit": 250, "financial_status": "paid"}
        if since:
            params["created_at_min"] = since

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(
                    f"{self._base_url()}/orders.json",
                    headers=self._headers(),
                    params=params,
                )
                resp.raise_for_status()
                orders = resp.json().get("orders", [])

            return [self._normalize_order(o) for o in orders]
        except httpx.HTTPStatusError as e:
            logger.error(f"Shopify fetch_orders HTTP error: {e.response.status_code} — {e.response.text[:200]}")
            return []
        except Exception as e:
            logger.error(f"Shopify fetch_orders error: {e}")
            return []

    def push_inventory_update(self, product_id: str, quantity: int) -> Dict:
        """Update inventory level for a product variant in Shopify."""
        # First get inventory_item_id for the variant (product_id = Shopify variant ID)
        try:
            with httpx.Client(timeout=30) as client:
                # Get variant to find inventory_item_id
                resp = client.get(
                    f"{self._base_url()}/variants/{product_id}.json",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                variant = resp.json().get("variant", {})
                inventory_item_id = variant.get("inventory_item_id")
                location_id = self.config.get("location_id")

                if not inventory_item_id or not location_id:
                    return {"success": False, "error": "Missing inventory_item_id or location_id"}

                # Set inventory level
                update_resp = client.post(
                    f"{self._base_url()}/inventory_levels/set.json",
                    headers=self._headers(),
                    json={
                        "location_id": location_id,
                        "inventory_item_id": inventory_item_id,
                        "available": quantity,
                    },
                )
                update_resp.raise_for_status()
                return {"success": True, "product_id": product_id, "synced_quantity": quantity}
        except Exception as e:
            logger.error(f"Shopify push_inventory_update error: {e}")
            return {"success": False, "error": str(e)}

    def health_check(self) -> Dict:
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(f"{self._base_url()}/shop.json", headers=self._headers())
                resp.raise_for_status()
                shop = resp.json().get("shop", {})
                return {"channel": self.get_channel_name(), "status": "healthy",
                        "shop": shop.get("name"), "domain": shop.get("domain")}
        except Exception as e:
            return {"channel": self.get_channel_name(), "status": "unhealthy", "error": str(e)}

    @staticmethod
    def _normalize_order(order: Dict) -> Dict:
        """Normalize Shopify order to StockPilot format."""
        return {
            "external_order_id": str(order["id"]),
            "external_order_number": order.get("order_number"),
            "channel": "shopify",
            "status": order.get("financial_status", "unknown"),
            "fulfillment_status": order.get("fulfillment_status"),
            "items": [
                {
                    "sku": item.get("sku", ""),
                    "variant_id": str(item.get("variant_id", "")),
                    "product_id": str(item.get("product_id", "")),
                    "title": item.get("title"),
                    "quantity": item.get("quantity", 0),
                    "price": float(item.get("price", 0)),
                }
                for item in order.get("line_items", [])
            ],
            "customer": {
                "name": f"{order.get('customer', {}).get('first_name', '')} {order.get('customer', {}).get('last_name', '')}".strip(),
                "email": order.get("email", ""),
                "phone": order.get("phone", ""),
            },
            "total_price": float(order.get("total_price", 0)),
            "currency": order.get("currency", "USD"),
            "created_at": order.get("created_at"),
        }
