from ellar.common.params import add_default_resolver
from ellar.common.params.resolvers.system_parameters import (
    ConnectionParam,
    RequestParameter,
    WebSocketParameter,
)
from starlette.requests import HTTPConnection, Request
from starlette.websockets import WebSocket

__all__ = ["HTTPConnection", "Request", "WebSocket"]

add_default_resolver(HTTPConnection, ConnectionParam)
add_default_resolver(Request, RequestParameter)
add_default_resolver(WebSocket, WebSocketParameter)
