"""
StockPilot Channel Connectors — multi-channel inventory & order sync.
Supported channels: Shopify, WooCommerce, Amazon (SP-API), Noon (GCC)
"""
from app.connectors.base_connector import BaseConnector
from app.connectors.shopify_connector import ShopifyConnector
from app.connectors.woocommerce_connector import WooCommerceConnector
from app.connectors.amazon_connector import AmazonConnector
from app.connectors.noon_connector import NoonConnector

CONNECTOR_REGISTRY = {
    "shopify": ShopifyConnector,
    "woocommerce": WooCommerceConnector,
    "amazon": AmazonConnector,
    "noon": NoonConnector,
}


def get_connector(channel: str, tenant_id: str, config: dict) -> BaseConnector:
    """Factory function to instantiate a connector by channel name."""
    connector_cls = CONNECTOR_REGISTRY.get(channel.lower())
    if not connector_cls:
        raise ValueError(f"Unknown channel: {channel}. Available: {list(CONNECTOR_REGISTRY.keys())}")
    return connector_cls(tenant_id, config)


__all__ = [
    "BaseConnector", "ShopifyConnector", "WooCommerceConnector",
    "AmazonConnector", "NoonConnector", "get_connector", "CONNECTOR_REGISTRY",
]
