import inspect
import typing as t
from abc import ABC

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
from starlette.routing import Mount

_socket_servers: t.Dict[str, socketio.AsyncServer] = {}


class GatewayRouterFactory(RouterBuilder, controller_type=type(GatewayBase)):
    @classmethod
    def _get_message_handler(
        cls,
        klass: t.Type,
    ) -> t.Iterable[t.Union[t.Callable]]:
        for method in klass.__dict__.values():
            if hasattr(method, MESSAGE_MAPPING_METADATA) and getattr(
                method, MESSAGE_MAPPING_METADATA
            ):
                yield method

    @classmethod
    def _process_controller_routes(
        cls, klass: t.Type[GatewayBase]
    ) -> t.List[t.Callable]:
        bases = inspect.getmro(klass)
        results = []

        if reflect.get_metadata(GATEWAY_METADATA.PROCESSED, klass):
            return reflect.get_metadata(GATEWAY_MESSAGE_HANDLER_KEY, klass) or []

        for base_cls in reversed(bases):
            if base_cls not in [ABC, GatewayBase, object]:
                for method in cls._get_message_handler(base_cls):
                    if reflect.has_metadata(CONTROLLER_CLASS_KEY, method):
                        raise Exception(
                            f"{klass.__name__} Gateway message handler tried to be processed more than once."
                            f"\n-Message Handler - {method}."
                            f"\n-Gateway message handler can not be reused once its under a `@Gateway` decorator."
                        )

                    results.append(method)

                    reflect.define_metadata(CONTROLLER_CLASS_KEY, klass, method)
                    reflect.define_metadata(
                        GATEWAY_MESSAGE_HANDLER_KEY, [method], klass
                    )

        reflect.define_metadata(GATEWAY_METADATA.PROCESSED, True, klass)
        return results

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

        socket_server = _socket_servers.get(path)

        if not socket_server:
            socket_server = socketio.AsyncServer(**options)
            _socket_servers.update({path: socket_server})

        for handler in cls._process_controller_routes(controller_type):
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

        return Mount(app=SocketIOASGIApp(socket_server), path=path, name=name)

    @classmethod
    def check_type(cls, controller_type: t.Union[t.Type, t.Any]) -> None:
        assert reflect.get_metadata(GATEWAY_WATERMARK, controller_type) and isinstance(
            controller_type, GatewayType
        ), "Invalid Gateway Type."
