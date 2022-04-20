from starlette.websockets import (  # noqa
    WebSocket as StarletteWebSocket,
    WebSocketClose,
    WebSocketDisconnect,
    WebSocketState,
)

from .http import HTTPConnection


class WebSocket(StarletteWebSocket, HTTPConnection):
    pass
