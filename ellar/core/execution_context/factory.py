import typing as t

from ellar.common.constants import empty_receive, empty_send
from ellar.common.exceptions import HostContextException
from ellar.common.interfaces import (
    IExecutionContext,
    IExecutionContextFactory,
    IHostContext,
    IHostContextFactory,
    IHTTPConnectionContextFactory,
    IWebSocketContextFactory,
)
from ellar.common.types import TReceive, TScope, TSend
from ellar.core.services import Reflector
from ellar.di import injectable

from .execution import ExecutionContext
from .host import HostContext
from .http import HTTPHostContext
from .websocket import WebSocketHostContext

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.routing import RouteOperationBase


@injectable()
class HTTPConnectionContextFactory(IHTTPConnectionContextFactory):
    context_type = HTTPHostContext

    def validate(self, context: IHostContext) -> None:
        """
        Validation is skipped here because HTTPConnection is compatible with websocket and http
        During websocket connection, we can still get HTTPConnection available,
        but we can get request instance or response.
        """
        pass


@injectable()
class WebSocketContextFactory(IWebSocketContextFactory):
    context_type = WebSocketHostContext

    def validate(self, context: IHostContext) -> None:
        if context.get_type() != "websocket":
            raise HostContextException(
                f"WebsocketConnection Context creation is not allow for scope[type]={context.get_type()}"
            )


@injectable()
class HostContextFactory(IHostContextFactory):
    __slots__ = ()

    def create_context(
        self, scope: TScope, receive: TReceive = empty_receive, send: TSend = empty_send
    ) -> IHostContext:
        host_context = HostContext(scope=scope, receive=receive, send=send)
        return host_context


@injectable()
class ExecutionContextFactory(IExecutionContextFactory):
    __slots__ = ("reflector",)

    def __init__(self, reflector: Reflector) -> None:
        self.reflector = reflector

    def create_context(
        self,
        operation: "RouteOperationBase",
        scope: TScope,
        receive: TReceive = empty_receive,
        send: TSend = empty_send,
    ) -> IExecutionContext:
        i_execution_context = ExecutionContext(
            scope=scope,
            receive=receive,
            send=send,
            operation_handler=operation.endpoint,
            operation_handler_type=operation.get_controller_type(),
            reflector=self.reflector,
        )

        return i_execution_context
