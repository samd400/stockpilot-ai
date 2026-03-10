"""
Amazon Selling Partner API (SP-API) Connector.
Config keys: marketplace_id, seller_id, lwa_client_id, lwa_client_secret, refresh_token, region
Supports: India (A21TJRUUN4KGV), UAE (A2VIGQ35RCS4UG), UK (A1F83G8C2ARO7P), DE (A1PA6795UKMFR9)
"""
import logging
import time
from typing import List, Dict, Optional

import httpx

from app.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)

MARKETPLACE_ENDPOINTS = {
    "A21TJRUUN4KGV": "sellingpartnerapi-fe.amazon.com",   # India
    "A2VIGQ35RCS4UG": "sellingpartnerapi-fe.amazon.com",  # UAE
    "A1F83G8C2ARO7P": "sellingpartnerapi-eu.amazon.com",  # UK
    "A1PA6795UKMFR9": "sellingpartnerapi-eu.amazon.com",  # Germany
    "ATVPDKIKX0DER":  "sellingpartnerapi-na.amazon.com",  # US
}

LWA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"


class AmazonConnector(BaseConnector):
    """
    Amazon SP-API connector for order fetching and FBM inventory management.
    Does NOT use the mock Marketplace API — uses real LWA tokens.
    """

    def __init__(self, tenant_id: str, config: Dict = None):
        super().__init__(tenant_id, config)
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0

    def get_channel_name(self) -> str:
        return "amazon"

    def _get_access_token(self) -> str:
        """Get or refresh LWA (Login with Amazon) access token."""
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        try:
            with httpx.Client(timeout=15) as client:
                resp = client.post(LWA_TOKEN_URL, data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.config["refresh_token"],
                    "client_id": self.config["lwa_client_id"],
                    "client_secret": self.config["lwa_client_secret"],
                })
                resp.raise_for_status()
                token_data = resp.json()
                self._access_token = token_data["access_token"]
                self._token_expires_at = time.time() + token_data.get("expires_in", 3600)
                return self._access_token
        except Exception as e:
            logger.error(f"Amazon LWA token refresh failed: {e}")
            raise

    def _base_url(self) -> str:
        marketplace_id = self.config.get("marketplace_id", "ATVPDKIKX0DER")
        endpoint = MARKETPLACE_ENDPOINTS.get(marketplace_id, "sellingpartnerapi-na.amazon.com")
        return f"https://{endpoint}"

    def _headers(self) -> Dict:
        return {
            "x-amz-access-token": self._get_access_token(),
            "Content-Type": "application/json",
        }

    def fetch_orders(self, since: Optional[str] = None) -> List[Dict]:
        """Fetch unshipped orders from Amazon SP-API."""
        marketplace_id = self.config.get("marketplace_id", "ATVPDKIKX0DER")
        params = {
            "MarketplaceIds": marketplace_id,
            "OrderStatuses": "Unshipped,PartiallyShipped",
        }
        if since:
            params["CreatedAfter"] = since

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(
                    f"{self._base_url()}/orders/v0/orders",
                    headers=self._headers(),
                    params=params,
                )
                resp.raise_for_status()
                result = resp.json()
                orders = result.get("payload", {}).get("Orders", [])

            # Fetch order items for each order
            enriched = []
            for order in orders[:50]:  # Limit to 50 to avoid throttling
                order_id = order["AmazonOrderId"]
                items = self._fetch_order_items(order_id)
                enriched.append(self._normalize_order(order, items))
            return enriched
        except Exception as e:
            logger.error(f"Amazon fetch_orders error: {e}")
            return []

    def _fetch_order_items(self, order_id: str) -> List[Dict]:
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(
                    f"{self._base_url()}/orders/v0/orders/{order_id}/orderItems",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                return resp.json().get("payload", {}).get("OrderItems", [])
        except Exception as e:
            logger.warning(f"Amazon fetch order items for {order_id} failed: {e}")
            return []

    def push_inventory_update(self, product_id: str, quantity: int) -> Dict:
        """
        Update FBM (Fulfilled by Merchant) inventory on Amazon.
        product_id = seller SKU
        """
        # Amazon inventory updates are done via Feeds API (submit XML/JSON feed)
        # This is a simplified implementation — full implementation requires XML feed
        logger.warning(
            f"Amazon inventory sync for {product_id}={quantity} — "
            "Full Feed API implementation required for production. "
            "Please use Amazon Seller Central or SP-API Feeds API."
        )
        return {
            "success": False,
            "product_id": product_id,
            "message": "Amazon inventory sync requires SP-API Feeds API. Manual sync required.",
        }

    def health_check(self) -> Dict:
        try:
            self._get_access_token()
            return {"channel": self.get_channel_name(), "status": "healthy",
                    "marketplace_id": self.config.get("marketplace_id")}
        except Exception as e:
            return {"channel": self.get_channel_name(), "status": "unhealthy", "error": str(e)}

    @staticmethod
    def _normalize_order(order: Dict, items: List[Dict]) -> Dict:
        buyer_info = order.get("BuyerInfo", {})
        return {
            "external_order_id": order["AmazonOrderId"],
            "channel": "amazon",
            "status": order.get("OrderStatus", "unknown"),
            "fulfillment_channel": order.get("FulfillmentChannel", "MFN"),
            "items": [
                {
                    "sku": item.get("SellerSKU", ""),
                    "asin": item.get("ASIN", ""),
                    "title": item.get("Title"),
                    "quantity": item.get("QuantityOrdered", 0),
                    "price": float(item.get("ItemPrice", {}).get("Amount", 0)),
                }
                for item in items
            ],
            "customer": {
                "name": buyer_info.get("BuyerName", ""),
                "email": buyer_info.get("BuyerEmail", ""),
            },
            "total_price": float(order.get("OrderTotal", {}).get("Amount", 0)),
            "currency": order.get("OrderTotal", {}).get("CurrencyCode", "USD"),
            "created_at": order.get("PurchaseDate"),
        }
