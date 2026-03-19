"""
Base connector class — all integrations inherit from this.
Each connector wraps a real external service with actual API calls.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """Abstract base for all real integrations."""

    service_name: str = ""
    display_name: str = ""
    description: str = ""
    icon: str = "🔌"
    category: str = "general"
    auth_type: str = "api_key"  # api_key | oauth2 | basic | smtp | webhook

    # Fields required for setup
    credential_fields: List[Dict] = []

    def __init__(self, credentials: dict):
        self.credentials = credentials
        self.logger = logging.getLogger(f"connector.{self.service_name}")

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Verify credentials are valid. Return {success, message}."""
        pass

    @abstractmethod
    def get_actions(self) -> List[Dict]:
        """Return list of available actions this connector supports."""
        pass

    @abstractmethod
    def get_triggers(self) -> List[Dict]:
        """Return list of trigger types this connector supports."""
        pass

    async def execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a named action with params. Override in subclass."""
        raise NotImplementedError(f"Action '{action}' not implemented in {self.service_name}")

    def _ok(self, data: Any = None, message: str = "Success") -> Dict:
        return {"success": True, "message": message, "data": data}

    def _err(self, message: str, details: Any = None) -> Dict:
        return {"success": False, "message": message, "details": details}


CONNECTOR_REGISTRY: Dict[str, type] = {}


def register_connector(cls):
    """Decorator to register a connector."""
    CONNECTOR_REGISTRY[cls.service_name] = cls
    return cls
