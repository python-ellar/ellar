import typing as t

from socketio import AsyncServer

from ellar.common.types import TReceive, TScope, TSend


class SocketIOASGIApp:
    def __init__(self, server: AsyncServer) -> None:
        self._server = server

    async def __call__(self, scope: TScope, receive: TReceive, send: TSend) -> t.Any:
        if scope["type"] in ["http", "websocket"]:
            await self._server.handle_request(scope, receive, send)
