import typing as t

from ellar.types import TReceive, TScope, TSend

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.di.providers import Provider


class ASGIArgs:
    __slots__ = ("scope", "receive", "send", "context")

    def __init__(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        self.scope = scope
        self.receive = receive
        self.send = send
        self.context: t.Dict[t.Type, "Provider"] = {}

    def get_args(self) -> t.Tuple[TScope, TReceive, TSend]:
        return self.scope, self.receive, self.send
