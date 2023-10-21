import typing as t


class WsResponse:
    __slots__ = ("_event", "_data", "_to", "_room")

    def __init__(
        self,
        event: str,
        data: t.Any,
        to: t.Optional[str] = None,
        room: t.Optional[str] = None,
    ):
        self._event = event
        self._data = data
        self._to = to
        self._room = room

    def dict(self) -> t.Dict:
        return {
            "event": self._event,
            "data": self._data,
            "to": self._to,
            "room": self._room,
        }
