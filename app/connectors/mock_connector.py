"""Mock Connector — example connector for testing multi-channel integration."""

import logging
from typing import List, Dict, Optional
from app.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)


class MockConnector(BaseConnector):
    """Mock connector that simulates an external sales channel (e.g., Shopify, WooCommerce)."""

    def get_channel_name(self) -> str:
        return "mock_channel"

    def fetch_orders(self, since: Optional[str] = None) -> List[Dict]:
        """Return simulated orders."""
        return [
            {
                "external_order_id": "MOCK-001",
                "items": [{"sku": "PROD-001", "quantity": 2, "price": 49.99}],
                "customer": {"name": "Test Customer", "email": "test@example.com"},
                "status": "paid",
            },
            {
                "external_order_id": "MOCK-002",
                "items": [{"sku": "PROD-002", "quantity": 1, "price": 29.99}],
                "customer": {"name": "Mock Customer", "email": "mock@example.com"},
                "status": "paid",
            },
        ]

    def push_inventory_update(self, product_id: str, quantity: int) -> Dict:
        """Simulate pushing inventory update."""
        logger.info(f"[MockConnector] Pushed inventory: product={product_id}, qty={quantity}")
        return {"success": True, "product_id": product_id, "synced_quantity": quantity}

    def health_check(self) -> Dict:
        return {"channel": self.get_channel_name(), "status": "healthy"}
