from ellar.common.params.args import add_default_resolver
from ellar.common.params.resolvers.non_parameter import (
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
