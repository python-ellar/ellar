from injector import CallableProvider
from starlette.requests import (
    HTTPConnection as StarletteHTTPConnection,
    Request as StarletteRequest,
)
from starlette.websockets import WebSocket as StarletteWebSocket

from ellar.di import EllarInjector, injectable
from ellar.di.exceptions import ServiceUnavailable
from ellar.services.reflector import Reflector

from .connection.http import HTTPConnection, Request
from .connection.websocket import WebSocket
from .context import (
    ExecutionContextFactory,
    HostContextFactory,
    IExecutionContext,
    IExecutionContextFactory,
    IHostContext,
    IHostContextFactory,
    IHTTPHostContext,
    IWebSocketHostContext,
)
from .context.factory import HTTPConnectionContextFactory, WebSocketContextFactory
from .exceptions.interfaces import IExceptionMiddlewareService
from .exceptions.service import ExceptionMiddlewareService
from .response import Response


class CoreServiceRegistration:
    """Create Binding for all application service"""

    __slots__ = ("injector",)

    def __init__(self, injector: EllarInjector) -> None:
        self.injector = injector

    def register_host_context(self) -> None:
        @injectable
        def resolve_host_context(
            host_context_factory: IHostContextFactory,
        ) -> IHostContext:
            return host_context_factory.create_context()

        self.injector.container.register_scoped(IHostContext, resolve_host_context)

    def register_execution_host_context(self) -> None:
        def resolve_execution_host_context() -> IHostContext:
            raise ServiceUnavailable("Service Unavailable at the current context.")

        self.injector.container.register_scoped(
            IExecutionContext, resolve_execution_host_context
        )

    def register_connection(self) -> None:
        @injectable
        def get_http_connection(http_host: IHTTPHostContext) -> HTTPConnection:
            return http_host.get_client()

        self.injector.container.register_scoped(
            HTTPConnection, CallableProvider(get_http_connection)
        )
        self.injector.container.register_scoped(
            StarletteHTTPConnection, CallableProvider(get_http_connection)
        )

    def register_request(self) -> None:
        @injectable
        def get_request_connection(http_host: IHTTPHostContext) -> Request:
            return http_host.get_request()

        self.injector.container.register_scoped(
            Request, CallableProvider(get_request_connection)
        )
        self.injector.container.register_scoped(
            StarletteRequest, CallableProvider(get_request_connection)
        )

    def register_response(self) -> None:
        @injectable
        def get_response(http_host: IHTTPHostContext) -> Response:
            return http_host.get_response()

        self.injector.container.register_scoped(
            Response, CallableProvider(get_response)
        )

    def register_websocket(self) -> None:
        @injectable
        def get_websocket_connection(
            websock_context: IWebSocketHostContext,
        ) -> WebSocket:
            return websock_context.get_client()

        websocket_context = CallableProvider(get_websocket_connection)
        self.injector.container.register_scoped(WebSocket, websocket_context)
        self.injector.container.register_scoped(StarletteWebSocket, websocket_context)

    def register_all(self) -> None:
        self.injector.container.register(
            IExceptionMiddlewareService, ExceptionMiddlewareService
        )

        self.injector.container.register(
            IExecutionContextFactory, ExecutionContextFactory
        )
        self.injector.container.register(IHostContextFactory, HostContextFactory)

        self.injector.container.register_scoped(
            IHTTPHostContext,
            HTTPConnectionContextFactory().__call__,
        )

        self.injector.container.register_scoped(
            IWebSocketHostContext,
            WebSocketContextFactory().__call__,
        )

        self.injector.container.register_instance(Reflector())
        self.register_host_context()
        self.register_execution_host_context()
        self.register_request()
        self.register_websocket()
        self.register_response()
        self.register_connection()
