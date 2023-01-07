import typing as t
from abc import ABC, abstractmethod

from ellar.constants import ASGI_CONTEXT_VAR
from ellar.di import injectable
from ellar.di.exceptions import ServiceUnavailable
from ellar.services import Reflector
from ellar.types import T

from .exceptions import HostContextException
from .execution import ExecutionContext
from .host import HostContext
from .http import HTTPHostContext
from .interface import (
    IExecutionContext,
    IExecutionContextFactory,
    IHostContext,
    IHostContextFactory,
)
from .websocket import WebSocketHostContext

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.routing import RouteOperationBase


class SubHostContextFactory(t.Generic[T], ABC):
    """
    Factory for creating HostContext types and validating them.
    """

    context_type: t.Type[T]

    __slots__ = ()

    @injectable()
    def __call__(self, context: IHostContext) -> T:
        self.validate(context)
        return self.create_context_type(context)

    @abstractmethod
    def validate(self, context: IHostContext) -> None:
        pass

    def create_context_type(self, context: IHostContext) -> T:
        scope, receive, send = context.get_args()
        return self.context_type(  # type:ignore
            scope=scope,
            receive=receive,
            send=send,
        )


class HTTPConnectionContextFactory(SubHostContextFactory[HTTPHostContext]):
    context_type = HTTPHostContext

    def validate(self, context: IHostContext) -> None:
        """
        Validation is skipped here because HTTPConnection is compatible with websocket and http
        During websocket connection, we can still get HTTPConnection available,
        but we can get request instance or response.
        """
        pass


class WebSocketContextFactory(SubHostContextFactory[WebSocketHostContext]):
    context_type = WebSocketHostContext

    def validate(self, context: IHostContext) -> None:
        if context.get_type() != "websocket":
            raise HostContextException(
                f"WebsocketConnection Context creation is not allow for scope[type]={context.get_type()}"
            )


@injectable()
class HostContextFactory(IHostContextFactory):
    __slots__ = ()

    def create_context(self) -> IHostContext:
        scoped_request_args = ASGI_CONTEXT_VAR.get()

        if not scoped_request_args:
            raise ServiceUnavailable()

        scope, receive, send = scoped_request_args.get_args()
        host_context = HostContext(scope=scope, receive=receive, send=send)
        host_context.get_service_provider().update_scoped_context(
            IHostContext, host_context  # type: ignore
        )
        return host_context


@injectable()
class ExecutionContextFactory(IExecutionContextFactory):
    __slots__ = ("reflector",)

    def __init__(self, reflector: Reflector) -> None:
        self.reflector = reflector

    def create_context(self, operation: "RouteOperationBase") -> IExecutionContext:
        scoped_request_args = ASGI_CONTEXT_VAR.get()

        if not scoped_request_args:
            raise ServiceUnavailable()

        scope, receive, send = scoped_request_args.get_args()
        i_execution_context = ExecutionContext(
            scope=scope,
            receive=receive,
            send=send,
            operation_handler=operation.endpoint,
            reflector=self.reflector,
        )
        i_execution_context.get_service_provider().update_scoped_context(
            IExecutionContext, i_execution_context  # type: ignore
        )

        return i_execution_context
