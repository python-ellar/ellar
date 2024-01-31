import typing as t

from ellar.reflect import reflect
from ellar.socket_io.constants import MESSAGE_MAPPING_METADATA, MESSAGE_METADATA
from ellar.utils import get_name


def subscribe_message(message: str) -> t.Callable:
    def _decorator(func: t.Callable) -> t.Callable:
        setattr(func, MESSAGE_MAPPING_METADATA, True)
        reflect.define_metadata(MESSAGE_METADATA, message, func)
        return func

    if callable(message):
        func = message
        message = get_name(func)
        return _decorator(t.cast(t.Callable, func))

    return _decorator
