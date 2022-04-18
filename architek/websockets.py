from starlette.websockets import (  # noqa
    WebSocket as StarletteWebSocket,
    WebSocketClose,
    WebSocketDisconnect,
    WebSocketState,
)

from architek.requests import HTTPConnection


class WebSocket(StarletteWebSocket, HTTPConnection):
    pass
