import typing as t

import socketio
from ellar.core.routing import RouterBuilder
from ellar.reflect import reflect
from ellar.socket_io.adapter import SocketIOASGIApp
from ellar.socket_io.constants import (
    CONNECTION_EVENT,
    DISCONNECT_EVENT,
    GATEWAY_MESSAGE_HANDLER_KEY,
    GATEWAY_METADATA,
    GATEWAY_OPTIONS,
    GATEWAY_WATERMARK,
    MESSAGE_METADATA,
)
from ellar.socket_io.gateway import SocketMessageOperation, SocketOperationConnection
from ellar.socket_io.model import GatewayBase, GatewayType
from starlette.routing import Mount

_socket_servers: t.Dict[str, socketio.AsyncServer] = {}


class GatewayRouterFactory(RouterBuilder, controller_type=type(GatewayBase)):
    @classmethod
    def build(
        cls, controller_type: t.Union[t.Type[GatewayBase], t.Any], **kwargs: t.Any
    ) -> "Mount":
        name = reflect.get_metadata_or_raise_exception(
            GATEWAY_METADATA.NAME, controller_type
        )
        path = reflect.get_metadata_or_raise_exception(
            GATEWAY_METADATA.PATH, controller_type
        )
        options = reflect.get_metadata_or_raise_exception(
            GATEWAY_OPTIONS, controller_type
        )
        message_handlers = (
            reflect.get_metadata(GATEWAY_MESSAGE_HANDLER_KEY, controller_type) or []
        )

        socket_server = _socket_servers.get(path)

        if not socket_server:
            socket_server = socketio.AsyncServer(**options)
            _socket_servers.update({path: socket_server})

        for handler in message_handlers:
            is_connection_handler = reflect.get_metadata(CONNECTION_EVENT, handler)
            is_disconnection_handler = reflect.get_metadata(DISCONNECT_EVENT, handler)

            if is_connection_handler:
                SocketOperationConnection(CONNECTION_EVENT, socket_server, handler)
            elif is_disconnection_handler:
                SocketOperationConnection(DISCONNECT_EVENT, socket_server, handler)
            else:
                message = reflect.get_metadata_or_raise_exception(
                    MESSAGE_METADATA, handler
                )
                SocketMessageOperation(message, socket_server, handler)

        router = Mount(app=SocketIOASGIApp(socket_server), path=path, name=name)
        return router

    @classmethod
    def check_type(cls, controller_type: t.Union[t.Type, t.Any]) -> None:
        assert reflect.get_metadata(GATEWAY_WATERMARK, controller_type) and isinstance(
            controller_type, GatewayType
        ), "Invalid Gateway Type."
