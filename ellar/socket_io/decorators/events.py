import typing as t

from ellar.reflect import reflect
from ellar.socket_io.constants import (
    CONNECTION_EVENT,
    DISCONNECT_EVENT,
    MESSAGE_MAPPING_METADATA,
)


def on_connected() -> t.Callable:
    def _decorator(func: t.Callable) -> t.Callable:
        setattr(func, MESSAGE_MAPPING_METADATA, True)
        reflect.define_metadata(CONNECTION_EVENT, True, func)
        return func

    return _decorator


def on_disconnected() -> t.Callable:
    def _decorator(func: t.Callable) -> t.Callable:
        setattr(func, MESSAGE_MAPPING_METADATA, True)
        reflect.define_metadata(DISCONNECT_EVENT, True, func)
        return func

    return _decorator
