import typing as t
from functools import wraps

from ellar.auth.guards import GuardAPIKeyHeader
from ellar.common import Header, Query, Serializer, UseGuards, WsBody, extra_args
from ellar.common.params import ExtraEndpointArg
from ellar.core.connection import HTTPConnection
from ellar.di import injectable
from ellar.socket_io import (
    WebSocketGateway,
    WsResponse,
    on_connected,
    on_disconnected,
    subscribe_message,
)
from ellar.socket_io.model import GatewayBase
from starlette import status
from starlette.exceptions import WebSocketException


def add_extra_args(func):
    # EXTRA ARGS SETUP
    query1 = ExtraEndpointArg(name="query1", annotation=str, default_value=Query())
    query2 = ExtraEndpointArg(
        name="query2", annotation=str
    )  # will default to Query during computation

    extra_args(query1, query2)(func)

    @wraps(func)
    def _wrapper(*args, **kwargs):
        # RESOLVING EXTRA ARGS
        # All extra args must be resolved before calling route function
        # else extra argument will be pushed to the route function
        resolved_query1 = query1.resolve(kwargs)
        resolved_query2 = query2.resolve(kwargs)

        return func(*args, **kwargs, query2=resolved_query2, query1=resolved_query1)

    return _wrapper


@injectable()
class HeaderGuard(GuardAPIKeyHeader):
    parameter_name = "x-auth-key"

    async def authentication_handler(
        self, connection: HTTPConnection, key: t.Optional[t.Any]
    ) -> t.Optional[t.Any]:
        if key == "supersecret":
            return key


class MessageData(Serializer):
    data: t.Any


class MessageRoom(Serializer):
    room: str


class MessageChatRoom(Serializer):
    room: str
    data: t.Any


@WebSocketGateway(path="/ws", async_mode="asgi", cors_allowed_origins="*")
class EventGateway:
    @subscribe_message("my_event")
    async def my_event(self, message: MessageData = WsBody()):
        return WsResponse("my_response", {"data": message.data}, room=self.context.sid)

    @subscribe_message
    async def my_broadcast_event(self, message: MessageData = WsBody()):
        await self.context.server.emit("my_response", {"data": message.data})

    @on_connected()
    async def connect(self):
        await self.context.server.emit(
            "my_response", {"data": "Connected", "count": 0}, room=self.context.sid
        )

    @on_disconnected()
    async def disconnect(self):
        print("Client disconnected")


@UseGuards(HeaderGuard)
@WebSocketGateway(path="/ws-guard")
class GatewayWithGuards(GatewayBase):
    @subscribe_message("my_event")
    async def my_event(self, message: MessageData = WsBody()):
        return WsResponse(
            "my_response",
            {
                "data": message.data,
                "auth-key": self.context.switch_to_http_connection().get_client().user,
            },
        )

    @subscribe_message("my_event_header")
    async def my_event_header(
        self,
        data: str = WsBody(..., embed=True),
        x_auth_key: str = Header(alias="x-auth-key"),
    ):
        return WsResponse("my_response", {"data": data, "x_auth_key": x_auth_key})

    @subscribe_message("my_plain_response")
    async def my_plain_response(
        self,
        data: str = WsBody(..., embed=True),
        x_auth_key: str = Header(alias="x-auth-key"),
    ):
        return {"data": data, "x_auth_key": x_auth_key}


@WebSocketGateway(path="/ws-others")
class GatewayOthers(GatewayBase):
    @subscribe_message("my_event")
    async def my_event(self, message: MessageData = WsBody()):
        raise Exception("I dont have anything to run.")

    @subscribe_message("my_event_raise")
    async def my_event_raise(self, message: MessageData = WsBody()):
        raise WebSocketException(
            code=status.WS_1009_MESSAGE_TOO_BIG, reason="Message is too big"
        )

    @subscribe_message("extra_args")
    @add_extra_args
    def extra_args_handler(self, query1: str, query2: str):
        raise WebSocketException(
            code=status.WS_1009_MESSAGE_TOO_BIG,
            reason={"query1": query1, "query2": query2},
        )
