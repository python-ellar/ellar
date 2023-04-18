import typing as t

from ellar.reflect import reflect
from ellar.socket_io.constants import MESSAGE_MAPPING_METADATA, MESSAGE_METADATA


def subscribe_message(message: str) -> t.Callable:
    def _decorator(func: t.Callable) -> t.Callable:
        setattr(func, MESSAGE_MAPPING_METADATA, True)
        reflect.define_metadata(MESSAGE_METADATA, message, func)
        return func

    return _decorator
