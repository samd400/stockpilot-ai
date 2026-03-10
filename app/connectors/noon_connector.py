"""
Noon.com Connector — GCC e-commerce marketplace.
Covers: UAE, Saudi Arabia, Egypt.
Config keys: access_key, channel (FBN or FBS), country_code (UAE, SAU, EGY)
Noon Seller API: https://sell.noon.com/seller-hub/api-documentation
"""
import logging
from typing import List, Dict, Optional

import httpx

from app.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)

NOON_API_URLS = {
    "UAE": "https://api.noon.com/seller/v1",
    "SAU": "https://api.noon.com/seller/v1",
    "EGY": "https://api.noon.com/seller/v1",
}


class NoonConnector(BaseConnector):
    """
    Noon.com GCC marketplace connector.
    Requires: config["access_key"], config["country_code"] (UAE/SAU/EGY)
    """

    def get_channel_name(self) -> str:
        return f"noon_{self.config.get('country_code', 'UAE').lower()}"

    def _base_url(self) -> str:
        country = self.config.get("country_code", "UAE")
        return NOON_API_URLS.get(country, NOON_API_URLS["UAE"])

    def _headers(self) -> Dict:
        return {
            "Authorization": f"Key {self.config['access_key']}",
            "Content-Type": "application/json",
        }

    def fetch_orders(self, since: Optional[str] = None) -> List[Dict]:
        """Fetch new orders from Noon Seller Hub API."""
        params = {"status": "created", "page_size": 100}
        if since:
            params["created_from"] = since

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(
                    f"{self._base_url()}/orders",
                    headers=self._headers(),
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()
                orders = data.get("orders", [])

            return [self._normalize_order(o) for o in orders]
        except httpx.HTTPStatusError as e:
            logger.error(f"Noon fetch_orders HTTP error: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Noon fetch_orders error: {e}")
            return []

    def push_inventory_update(self, product_id: str, quantity: int) -> Dict:
        """Update inventory quantity on Noon for a product SKU."""
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.put(
                    f"{self._base_url()}/catalog/product/inventory",
                    headers=self._headers(),
                    json={
                        "sku": product_id,
                        "quantity": quantity,
                    },
                )
                resp.raise_for_status()
                return {"success": True, "product_id": product_id, "synced_quantity": quantity}
        except Exception as e:
            logger.error(f"Noon push_inventory_update error: {e}")
            return {"success": False, "error": str(e)}

    def health_check(self) -> Dict:
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(f"{self._base_url()}/account/info", headers=self._headers())
                resp.raise_for_status()
                return {"channel": self.get_channel_name(), "status": "healthy",
                        "country": self.config.get("country_code")}
        except Exception as e:
            return {"channel": self.get_channel_name(), "status": "unhealthy", "error": str(e)}

    @staticmethod
    def _normalize_order(order: Dict) -> Dict:
        customer = order.get("customer", {})
        return {
            "external_order_id": str(order.get("id", "")),
            "external_order_number": order.get("order_number"),
            "channel": "noon",
            "status": order.get("status", "unknown"),
            "items": [
                {
                    "sku": item.get("sku", ""),
                    "noon_id": item.get("noon_id"),
                    "title": item.get("product_name"),
                    "quantity": item.get("qty", 0),
                    "price": float(item.get("unit_price", 0)),
                }
                for item in order.get("items", [])
            ],
            "customer": {
                "name": customer.get("name", ""),
                "email": customer.get("email", ""),
                "phone": customer.get("phone", ""),
            },
            "total_price": float(order.get("total_amount", 0)),
            "currency": order.get("currency", "AED"),
            "created_at": order.get("created_at"),
        }
