from ellar.common.params import add_default_resolver
from ellar.common.params.resolvers.system_parameters import (
    ConnectionParam,
    RequestParameter,
    WebSocketParameter,
)

from .http import HTTPConnection, Request
from .websocket import WebSocket

__all__ = ["HTTPConnection", "Request", "WebSocket"]

add_default_resolver(HTTPConnection, ConnectionParam)
add_default_resolver(Request, RequestParameter)
add_default_resolver(WebSocket, WebSocketParameter)
