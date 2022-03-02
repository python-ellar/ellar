import typing as t
from starlette.background import BackgroundTasks
from starletteapi.di.providers import CallableProvider
from starletteapi.requests import Request, HTTPConnection
from starletteapi.responses import Response
from starletteapi.types import TScope, TReceive, TSend
from starletteapi.websockets import WebSocket

from .compatible import cached_property

if t.TYPE_CHECKING:
    from starletteapi.main import StarletteApp
    from starletteapi.di.injector import DIRequestServiceProvider
    from starletteapi.routing.operations import OperationBase


class ExecutionContextException(Exception):
    pass


class ExecutionContext:
    __slots__ = ('scope', 'receive', 'send', '_operation', '_response', '__dict__')

    def __init__(self, *, scope: TScope, receive: TReceive, send: TSend, operation: 'OperationBase'):
        self.scope = scope
        self.receive = receive
        self.send = send
        self._operation = operation
        self._response: t.Optional[Response] = None

    @property
    def operation(self):
        return self._operation

    @property
    def has_response(self) -> bool:
        return self._response is not None

    @cached_property
    def _service_provider(self) -> t.Optional['DIRequestServiceProvider']:
        service_provider = self.switch_to_http_connection().service_provider
        if ExecutionContext not in service_provider.context:
            service_provider.update_context(ExecutionContext, self)
            service_provider.update_context(HTTPConnection, CallableProvider(self.switch_to_http_connection))
            service_provider.update_context(WebSocket, CallableProvider(self.switch_to_websocket))
            service_provider.update_context(Request, CallableProvider(self.switch_to_request))
            service_provider.update_context(Response, CallableProvider(self.get_response))
        return service_provider

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

    def get_service_provider(self) -> "DIRequestServiceProvider":
        return self._service_provider

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
