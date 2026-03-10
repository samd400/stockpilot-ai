"""
WooCommerce Connector — syncs orders via WooCommerce REST API v3.
Config keys: store_url, consumer_key, consumer_secret
"""
import logging
from typing import List, Dict, Optional

import httpx

from app.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)


class WooCommerceConnector(BaseConnector):
    """
    Production WooCommerce connector.
    Requires: config["store_url"], config["consumer_key"], config["consumer_secret"]
    """

    def get_channel_name(self) -> str:
        return "woocommerce"

    def _base_url(self) -> str:
        url = self.config["store_url"].rstrip("/")
        return f"{url}/wp-json/wc/v3"

    def _auth(self):
        return (self.config["consumer_key"], self.config["consumer_secret"])

    def fetch_orders(self, since: Optional[str] = None) -> List[Dict]:
        """Fetch processing orders from WooCommerce."""
        params = {"status": "processing", "per_page": 100, "orderby": "date", "order": "desc"}
        if since:
            params["after"] = since

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(
                    f"{self._base_url()}/orders",
                    auth=self._auth(),
                    params=params,
                )
                resp.raise_for_status()
                orders = resp.json()

            return [self._normalize_order(o) for o in orders]
        except httpx.HTTPStatusError as e:
            logger.error(f"WooCommerce fetch_orders HTTP error: {e.response.status_code} — {e.response.text[:200]}")
            return []
        except Exception as e:
            logger.error(f"WooCommerce fetch_orders error: {e}")
            return []

    def push_inventory_update(self, product_id: str, quantity: int) -> Dict:
        """Update WooCommerce product stock quantity."""
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.put(
                    f"{self._base_url()}/products/{product_id}",
                    auth=self._auth(),
                    json={"stock_quantity": quantity, "manage_stock": True},
                )
                resp.raise_for_status()
                return {"success": True, "product_id": product_id, "synced_quantity": quantity}
        except Exception as e:
            logger.error(f"WooCommerce push_inventory_update error: {e}")
            return {"success": False, "error": str(e)}

    def health_check(self) -> Dict:
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(f"{self._base_url()}/system_status", auth=self._auth())
                resp.raise_for_status()
                return {"channel": self.get_channel_name(), "status": "healthy",
                        "store_url": self.config.get("store_url")}
        except Exception as e:
            return {"channel": self.get_channel_name(), "status": "unhealthy", "error": str(e)}

    @staticmethod
    def _normalize_order(order: Dict) -> Dict:
        billing = order.get("billing", {})
        return {
            "external_order_id": str(order["id"]),
            "external_order_number": order.get("number"),
            "channel": "woocommerce",
            "status": order.get("status", "unknown"),
            "items": [
                {
                    "sku": item.get("sku", ""),
                    "product_id": str(item.get("product_id", "")),
                    "variation_id": str(item.get("variation_id", "")),
                    "title": item.get("name"),
                    "quantity": item.get("quantity", 0),
                    "price": float(item.get("price", 0)),
                }
                for item in order.get("line_items", [])
            ],
            "customer": {
                "name": f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip(),
                "email": billing.get("email", ""),
                "phone": billing.get("phone", ""),
            },
            "total_price": float(order.get("total", 0)),
            "currency": order.get("currency", "USD"),
            "created_at": order.get("date_created"),
        }
