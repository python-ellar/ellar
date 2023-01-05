import typing as t
from abc import ABC, abstractmethod

from ellar.types import T

from .exceptions import HostContextException
from .http import HTTPHostContext
from .interface import IHostContext
from .websocket import WebSocketHostContext


class HostContextFactory(t.Generic[T], ABC):
    """
    Factory for creating HostContext types and validating them.
    """

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


class HTTPConnectionContextFactory(HostContextFactory[HTTPHostContext]):
    context_type = HTTPHostContext

    def validate(self) -> None:
        """
        Validation is skipped here because HTTPConnection is compatible with websocket and http
        During websocket connection, we can still get HTTPConnection available,
        but we can get request instance or response.
        """
        pass


class WebSocketContextFactory(HostContextFactory[WebSocketHostContext]):
    context_type = WebSocketHostContext

    def validate(self) -> None:
        if self.context.get_type() != "websocket":
            raise HostContextException(
                f"WebsocketConnection Context creation is not allow for scope[type]={self.context.get_type()}"
            )
