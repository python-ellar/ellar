from ellar.compatible import cached_property
from ellar.core.connection import WebSocket
from ellar.types import TReceive, TScope, TSend

from .interface import IWebSocketHostContext


class WebSocketHostContext(IWebSocketHostContext):
    """
    Provides a context around websocket session
    """

    __slots__ = (
        "scope",
        "receive",
        "send",
    )

    def __init__(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        self.scope = scope
        self.receive = receive
        self.send = send

    @cached_property
    def _websocket_connection(self) -> WebSocket:
        return WebSocket(scope=self.scope, receive=self.receive, send=self.send)

    def get_client(self) -> WebSocket:
        return self._websocket_connection  # type: ignore
