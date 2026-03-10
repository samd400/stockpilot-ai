"""Base Connector — abstract interface for multi-channel inventory integrations."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseConnector(ABC):
    """Abstract base class for external sales channel connectors."""

    def __init__(self, tenant_id: str, config: Dict = None):
        self.tenant_id = tenant_id
        self.config = config or {}

    @abstractmethod
    def fetch_orders(self, since: Optional[str] = None) -> List[Dict]:
        """Fetch new orders from the external channel."""
        ...

    @abstractmethod
    def push_inventory_update(self, product_id: str, quantity: int) -> Dict:
        """Push inventory update to the external channel."""
        ...

    @abstractmethod
    def get_channel_name(self) -> str:
        """Return the name of this channel."""
        ...

    def health_check(self) -> Dict:
        """Check connectivity to the external system."""
        return {"channel": self.get_channel_name(), "status": "unknown"}
