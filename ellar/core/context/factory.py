import typing as t
from abc import ABC, abstractmethod

from ellar.types import T

from .exceptions import HostContextException
from .http import HTTPConnectionHost
from .interface import IHostContext
from .websocket import WebSocketConnectionHost


class HostContextFactory(t.Generic[T], ABC):
    context_type: t.Type[T]

    __slots__ = ("context", "_context_type", "validate_func")

    def __init__(
        self,
        context: IHostContext,
    ) -> None:
        self.context = context

    def __call__(self) -> T:
        self.validate()
        return self.create_context_type()

    @abstractmethod
    def validate(self) -> None:
        pass

    def create_context_type(self) -> T:
        scope, receive, send = self.context.get_args()
        return self.context_type(  # type:ignore
            scope=scope,
            receive=receive,
            send=send,
        )


class HTTPConnectionContextFactory(HostContextFactory[HTTPConnectionHost]):
    context_type = HTTPConnectionHost

    def validate(self) -> None:
        pass


class WebSocketContextFactory(HostContextFactory[WebSocketConnectionHost]):
    context_type = WebSocketConnectionHost

    def validate(self) -> None:
        if self.context.get_type() != "websocket":
            raise HostContextException(
                f"WebsocketConnection Context creation is not allow for scope[type]={self.context.get_type()}"
            )
