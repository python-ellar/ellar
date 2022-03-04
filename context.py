import typing as t
from starlette.background import BackgroundTasks
from starletteapi.requests import Request, HTTPConnection
from starletteapi.responses import Response
from starletteapi.types import TScope, TReceive, TSend
from starletteapi.websockets import WebSocket

from .compatible import cached_property, DataMapper, AttributeDictAccess
from .shortcuts import fail_silently

if t.TYPE_CHECKING:
    from starletteapi.main import StarletteApp
    from starletteapi.di.injector import RequestServiceProvider
    from starletteapi.routing.operations import OperationBase


class ExecutionContextException(Exception):
    pass


class OperationExecutionMeta(DataMapper, AttributeDictAccess):
    pass


class ExecutionContext:
    __slots__ = ('scope', 'receive', 'send', '_operation', '_response', '__dict__')

    def __init__(self, *, scope: TScope, receive: TReceive, send: TSend, operation: t.Optional['OperationBase'] = None):
        self.scope = scope
        self.receive = receive
        self.send = send
        self._operation: OperationExecutionMeta = OperationExecutionMeta(
            **operation.get_meta() if operation else {}
        )
        self._response: t.Optional[Response] = None

    @property
    def operation(self) -> OperationExecutionMeta:
        return self._operation

    @operation.setter
    def operation(self, value: 'OperationBase') -> None:
        self._operation = OperationExecutionMeta(
            **value.get_meta()
        )

    @property
    def has_response(self) -> bool:
        return self._response is not None

    @cached_property
    def _http_connection(self) -> HTTPConnection:
        return HTTPConnection(self.scope, receive=self.receive)

    @cached_property
    def _request(self) -> Request:
        if self.scope['type'] != 'http':
            raise ExecutionContextException(f"Context Switch is not allow for scope[type]={self.scope['type']}")
        return Request(self.scope, receive=self.receive, send=self.send)

    @cached_property
    def _websocket(self) -> WebSocket:
        if self.scope['type'] != 'websocket':
            raise ExecutionContextException(f"Context Switch is not allow for scope[type]={self.scope['type']}")
        return WebSocket(self.scope, receive=self.receive, send=self.send)

    def get_service_provider(self) -> "RequestServiceProvider":
        return self.switch_to_http_connection().service_provider

    def switch_to_request(self) -> Request:
        return self._request

    def switch_to_http_connection(self) -> HTTPConnection:
        return self._http_connection

    def switch_to_websocket(self) -> WebSocket:
        return self._websocket

    def get_response(self) -> Response:
        if not self._response:
            self._response = Response(
                background=BackgroundTasks(),
                content=None,
                status_code=-100,
                headers=None,  # type: ignore # in Starlette
                media_type=None,  # type: ignore # in Starlette
            )
        return self._response

    def get_app(self) -> 'StarletteApp':
        return t.cast('StarletteApp', self.scope["app"])

    @classmethod
    def create_context(
            cls,
            *,
            scope: TScope,
            receive: TReceive,
            send: TSend,
            operation: t.Optional['OperationBase'] = None
    ) -> 'ExecutionContext':
        connection = HTTPConnection(scope=scope)
        context = fail_silently(connection.service_provider.get, interface=ExecutionContext)
        if context:
            context.operation = operation
            return context
        return cls(scope=scope, receive=receive, send=send, operation=operation)
