import typing as t

import socketio
from starlette.routing import Mount

from ellar.reflect import reflect
from ellar.socket_io.adapter import SocketIOASGIApp
from ellar.socket_io.constants import (
    CONNECTION_EVENT,
    DISCONNECT_EVENT,
    GATEWAY_MESSAGE_HANDLER_KEY,
    GATEWAY_METADATA,
    GATEWAY_OPTIONS,
    MESSAGE_METADATA,
)
from ellar.socket_io.gateway import SocketMessageOperation, SocketOperationConnection
from ellar.socket_io.model import GatewayBase


def gateway_router_factory(
    gateway_type: t.Union[t.Type[GatewayBase], t.Any]
) -> "Mount":
    name = reflect.get_metadata_or_raise_exception(GATEWAY_METADATA.NAME, gateway_type)
    path = reflect.get_metadata_or_raise_exception(GATEWAY_METADATA.PATH, gateway_type)
    options = reflect.get_metadata_or_raise_exception(GATEWAY_OPTIONS, gateway_type)
    message_handlers = (
        reflect.get_metadata(GATEWAY_MESSAGE_HANDLER_KEY, gateway_type) or []
    )

    socket_server = socketio.AsyncServer(**options)

    for handler in message_handlers:
        is_connection_handler = reflect.get_metadata(CONNECTION_EVENT, handler)
        is_disconnection_handler = reflect.get_metadata(DISCONNECT_EVENT, handler)

        if is_connection_handler:
            SocketOperationConnection(CONNECTION_EVENT, socket_server, handler)
        elif is_disconnection_handler:
            SocketOperationConnection(DISCONNECT_EVENT, socket_server, handler)
        else:
            message = reflect.get_metadata_or_raise_exception(MESSAGE_METADATA, handler)
            SocketMessageOperation(message, socket_server, handler)

    # include_in_schema = reflect.get_metadata_or_raise_exception(
    #     GATEWAY_METADATA.INCLUDE_IN_SCHEMA, gateway_type
    # )
    router = Mount(app=SocketIOASGIApp(socket_server), path=path, name=name)
    return router
