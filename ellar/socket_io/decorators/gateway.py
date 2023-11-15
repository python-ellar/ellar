import inspect
import typing as t
from abc import ABC

from ellar.common.compatible import AttributeDict
from ellar.common.constants import CONTROLLER_CLASS_KEY
from ellar.common.exceptions import ImproperConfiguration
from ellar.common.utils import get_name
from ellar.di import RequestScope, injectable
from ellar.reflect import REFLECT_TYPE, reflect
from ellar.socket_io.constants import (
    GATEWAY_MESSAGE_HANDLER_KEY,
    GATEWAY_METADATA,
    GATEWAY_OPTIONS,
    GATEWAY_WATERMARK,
    MESSAGE_MAPPING_METADATA,
)
from ellar.socket_io.model import GatewayBase, GatewayType


def _get_message_handler(
    cls: t.Type,
) -> t.Iterable[t.Union[t.Callable]]:
    for method in cls.__dict__.values():
        if hasattr(method, MESSAGE_MAPPING_METADATA) and getattr(
            method, MESSAGE_MAPPING_METADATA
        ):
            yield method


def _reflect_all_controller_type_routes(cls: t.Type[GatewayBase]) -> None:
    bases = inspect.getmro(cls)

    for base_cls in reversed(bases):
        if base_cls not in [ABC, GatewayBase, object]:
            for method in _get_message_handler(base_cls):
                if reflect.has_metadata(CONTROLLER_CLASS_KEY, method):
                    raise Exception(
                        f"{cls.__name__} Gateway message handler tried to be processed more than once."
                        f"\n-Message Handler - {method}."
                        f"\n-Gateway message handler can not be reused once its under a `@Gateway` decorator."
                    )

                reflect.define_metadata(CONTROLLER_CLASS_KEY, cls, method)
                reflect.define_metadata(GATEWAY_MESSAGE_HANDLER_KEY, [method], cls)


def WebSocketGateway(
    path: str = "/socket.io", name: t.Optional[str] = None, **kwargs: str
) -> t.Callable:
    kwargs.setdefault("async_mode", "asgi")
    kwargs.setdefault("cors_allowed_origins", "*")

    def _decorator(cls: t.Type) -> t.Type:
        assert path == "" or path.startswith("/"), "Routed paths must start with '/'"
        _kwargs = AttributeDict(
            socket_init_kwargs=dict(kwargs),
            path=path,
            name=name,
            include_in_schema=False,
        )

        if not isinstance(cls, type):
            raise ImproperConfiguration(
                f"WebSocketGateway is a class decorator - {cls}"
            )

        _gateway_type = t.cast(t.Type[GatewayBase], cls)
        new_cls = None

        if type(_gateway_type) is not GatewayType:
            # We force the cls to inherit from `ControllerBase` by creating another type.
            attrs = {}
            if hasattr(cls, REFLECT_TYPE):
                attrs.update({REFLECT_TYPE: cls.__dict__[REFLECT_TYPE]})
            new_cls = type(cls.__name__, (cls, GatewayBase), attrs)

            _gateway_type = t.cast(t.Type[GatewayBase], new_cls)

        if not _kwargs["name"]:
            _kwargs["name"] = (
                str(get_name(_gateway_type)).lower().replace("gateway", "")
            )

        if not reflect.has_metadata(GATEWAY_WATERMARK, _gateway_type) and not hasattr(
            _gateway_type, "__GATEWAY_WATERMARK__"
        ):
            reflect.define_metadata(GATEWAY_WATERMARK, True, _gateway_type)
            reflect.define_metadata(
                GATEWAY_OPTIONS, _kwargs["socket_init_kwargs"], _gateway_type
            )
            _reflect_all_controller_type_routes(_gateway_type)
            injectable(RequestScope)(_gateway_type)

            for key in GATEWAY_METADATA.keys:
                reflect.define_metadata(key, _kwargs[key], _gateway_type)

        if new_cls:
            _gateway_type.__GATEWAY_WATERMARK__ = True  # type:ignore[attr-defined]

        return _gateway_type

    if callable(path):
        func = path
        path = "/socket.io"
        return _decorator(func)  # type:ignore[arg-type]
    return _decorator
