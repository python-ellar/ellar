try:
    import socketio  # noqa
except Exception as e:  # pragma: no cover
    raise Exception(
        "socketio package is required. Use `pip install python-socketio`."
    ) from e

from .decorators import (
    WebSocketGateway,
    on_connected,
    on_disconnected,
    subscribe_message,
)
from .factory import GatewayRouterFactory
from .model import GatewayBase
from .responses import WsResponse
from .testing import TestGateway

__all__ = [
    "WsResponse",
    "GatewayRouterFactory",
    "on_disconnected",
    "on_connected",
    "subscribe_message",
    "WebSocketGateway",
    "TestGateway",
    "GatewayBase",
]
