import typing as t

import socketio
from ellar.common.constants import CONTROLLER_CLASS_KEY
from ellar.core.router_builders import RouterBuilder
from ellar.reflect import reflect
from ellar.socket_io.adapter import SocketIOASGIApp
from ellar.socket_io.constants import (
    CONNECTION_EVENT,
    DISCONNECT_EVENT,
    GATEWAY_MESSAGE_HANDLER_KEY,
    GATEWAY_METADATA,
    GATEWAY_OPTIONS,
    GATEWAY_WATERMARK,
    MESSAGE_MAPPING_METADATA,
    MESSAGE_METADATA,
)
from ellar.socket_io.gateway import SocketMessageOperation, SocketOperationConnection
from ellar.socket_io.model import GatewayBase, GatewayType
from ellar.utils import get_functions_with_tag
from starlette.routing import Mount

_socket_servers: t.Dict[str, socketio.AsyncServer] = {}


class GatewayRouterFactory(RouterBuilder, controller_type=type(GatewayBase)):
    @classmethod
    def _process_controller_routes(
        cls, klass: t.Type[GatewayBase]
    ) -> t.List[t.Callable]:
        # bases = inspect.getmro(klass)
        results = []

        if reflect.get_metadata(GATEWAY_METADATA.PROCESSED, klass):
            return reflect.get_metadata(GATEWAY_MESSAGE_HANDLER_KEY, klass) or []

        for _name, method in get_functions_with_tag(
            klass, tag=MESSAGE_MAPPING_METADATA
        ):
            results.append(method)

            reflect.define_metadata(GATEWAY_MESSAGE_HANDLER_KEY, [method], klass)

        reflect.define_metadata(GATEWAY_METADATA.PROCESSED, True, klass)
        return results

    @classmethod
    def build(
        cls,
        controller_type: t.Union[t.Type[GatewayBase], t.Any],
        base_route_type: t.Type[Mount] = Mount,
        **kwargs: t.Any,
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

        socket_server = _socket_servers.get(path)

        if not socket_server:
            socket_server = socketio.AsyncServer(**options)
            _socket_servers.update({path: socket_server})

        for handler in cls._process_controller_routes(controller_type):
            is_connection_handler = reflect.get_metadata(CONNECTION_EVENT, handler)
            is_disconnection_handler = reflect.get_metadata(DISCONNECT_EVENT, handler)

            if is_connection_handler:
                SocketOperationConnection(
                    controller_type, CONNECTION_EVENT, socket_server, handler
                )
            elif is_disconnection_handler:
                SocketOperationConnection(
                    controller_type, DISCONNECT_EVENT, socket_server, handler
                )
            else:
                message = reflect.get_metadata_or_raise_exception(
                    MESSAGE_METADATA, handler
                )
                SocketMessageOperation(controller_type, message, socket_server, handler)

        mount = base_route_type(
            app=SocketIOASGIApp(socket_server), path=path, name=name
        )
        reflect.define_metadata(CONTROLLER_CLASS_KEY, controller_type, mount)
        return mount

    @classmethod
    def check_type(cls, controller_type: t.Union[t.Type, t.Any]) -> None:
        assert reflect.get_metadata(GATEWAY_WATERMARK, controller_type) and isinstance(
            controller_type, GatewayType
        ), "Invalid Gateway Type."
