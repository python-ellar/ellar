import typing as t

from ellar.core.serializer import Serializer


class WsResponse(Serializer):
    event: str
    data: t.Any
    to: t.Optional[str] = None
    room: t.Optional[str] = None
