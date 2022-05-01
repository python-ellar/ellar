import typing as t

from starlette.background import BackgroundTasks

from ellar.compatible import cached_property
from ellar.core.connection import HTTPConnection, Request, WebSocket
from ellar.core.response import Response
from ellar.shortcuts import fail_silently
from ellar.types import TReceive, TScope, TSend

from .interface import (
    ExecutionContextException,
    IExecutionContext,
    OperationExecutionMeta,
)

if t.TYPE_CHECKING:
    from ellar.core.main import App
    from ellar.core.routing import RouteOperationBase
    from ellar.core.routing.controller import ControllerBase
    from ellar.di.injector import RequestServiceProvider

__all__ = ["IExecutionContext", "ExecutionContext"]


class ExecutionContext(IExecutionContext):
    __slots__ = (
        "scope",
        "receive",
        "send",
        "_operation",
        "_response",
        "controller_type",
    )

    def __init__(
        self,
        *,
        scope: TScope,
        receive: TReceive,
        send: TSend,
        operation: t.Optional["RouteOperationBase"] = None,
    ) -> None:
        self.scope = scope
        self.receive = receive
        self.send = send
        self._operation: OperationExecutionMeta = OperationExecutionMeta(
            **operation.get_meta() if operation else {}
        )
        self._response: t.Optional[Response] = None
        self.controller_type: t.Optional[t.Type["ControllerBase"]] = getattr(
            operation or {}, "controller_type", None
        )

    @property
    def operation(self) -> OperationExecutionMeta:
        return self._operation

    def set_operation(self, operation: t.Optional["RouteOperationBase"] = None) -> None:
        if operation:
            self._operation = OperationExecutionMeta(**operation.get_meta())
            self.controller_type = getattr(operation, "controller_type", None)

    @property
    def has_response(self) -> bool:
        return self._response is not None

    @cached_property
    def _http_connection(self) -> HTTPConnection:
        return HTTPConnection(self.scope, receive=self.receive)

    @cached_property
    def _request(self) -> Request:
        if self.scope["type"] != "http":
            raise ExecutionContextException(
                f"Context Switch is not allow for scope[type]={self.scope['type']}"
            )
        return Request(self.scope, receive=self.receive, send=self.send)

    @cached_property
    def _websocket(self) -> WebSocket:
        if self.scope["type"] != "websocket":
            raise ExecutionContextException(
                f"Context Switch is not allow for scope[type]={self.scope['type']}"
            )
        return WebSocket(self.scope, receive=self.receive, send=self.send)

    def get_service_provider(self) -> "RequestServiceProvider":
        return self.switch_to_http_connection().service_provider

    def switch_to_request(self) -> Request:
        return t.cast(Request, self._request)

    def switch_to_http_connection(self) -> HTTPConnection:
        return t.cast(HTTPConnection, self._http_connection)

    def switch_to_websocket(self) -> WebSocket:
        return t.cast(WebSocket, self._websocket)

    def get_response(self) -> Response:
        if not self._response:
            self._response = Response(
                background=BackgroundTasks(),
                content=None,
                status_code=-100,
                headers=None,
                media_type=None,
            )
        return self._response

    def get_app(self) -> "App":
        return t.cast("App", self.scope["app"])

    @classmethod
    def create_context(
        cls,
        *,
        scope: TScope,
        receive: TReceive,
        send: TSend,
        operation: t.Optional["RouteOperationBase"] = None,
    ) -> "ExecutionContext":
        connection = HTTPConnection(scope=scope)
        context = t.cast(
            ExecutionContext,
            fail_silently(connection.service_provider.get, interface=ExecutionContext),
        )
        if context:
            context.set_operation(operation)
            return context
        return cls(scope=scope, receive=receive, send=send, operation=operation)
