import typing as t

from injector import CallableProvider
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.requests import (
    HTTPConnection as StarletteHTTPConnection,
    Request as StarletteRequest,
)
from starlette.responses import JSONResponse
from starlette.websockets import WebSocket as StarletteWebSocket

from ellar.constants import (
    SCOPE_HOST_CONTEXT_PROVIDER,
    SCOPE_RESPONSE_STARTED,
    SCOPE_SERVICE_PROVIDER,
)
from ellar.core.connection.http import HTTPConnection, Request
from ellar.core.connection.websocket import WebSocket
from ellar.core.context import (
    HostContext,
    IHostContext,
    IHTTPConnectionHost,
    IWebSocketConnectionHost,
)
from ellar.core.context.factory import (
    HTTPConnectionContextFactory,
    WebSocketContextFactory,
)
from ellar.core.response import Response
from ellar.types import ASGIApp, TMessage, TReceive, TScope, TSend

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.exceptions.interfaces import IExceptionHandler
    from ellar.di.injector import EllarInjector, RequestServiceProvider


class RequestServiceProviderMiddleware(ServerErrorMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        *,
        debug: bool,
        injector: "EllarInjector",
        handler: "IExceptionHandler" = None
    ) -> None:
        _handler = None
        if handler:
            self._500_error_handler = handler
            _handler = self.error_handler
        super(RequestServiceProviderMiddleware, self).__init__(
            debug=debug, handler=_handler, app=app
        )
        self.injector = injector

    @classmethod
    def _register_connection(cls, service_provider: "RequestServiceProvider") -> None:
        def get_http_connection() -> HTTPConnection:
            http_connection_context = service_provider.get(IHTTPConnectionHost)  # type: ignore
            return http_connection_context.get_client()

        service_provider.register(HTTPConnection, CallableProvider(get_http_connection))
        service_provider.register(
            StarletteHTTPConnection, CallableProvider(get_http_connection)
        )

    @classmethod
    def _register_request(cls, service_provider: "RequestServiceProvider") -> None:
        def get_request_connection() -> Request:
            http_connection_context = service_provider.get(IHTTPConnectionHost)  # type: ignore
            return http_connection_context.get_request()

        service_provider.register(Request, CallableProvider(get_request_connection))
        service_provider.register(
            StarletteRequest, CallableProvider(get_request_connection)
        )

    @classmethod
    def _register_response(cls, service_provider: "RequestServiceProvider") -> None:
        def get_response() -> Response:
            http_connection_context = service_provider.get(IHTTPConnectionHost)  # type: ignore
            return http_connection_context.get_response()

        service_provider.register(Response, CallableProvider(get_response))

    @classmethod
    def _register_websocket(cls, service_provider: "RequestServiceProvider") -> None:
        def get_websocket_connection() -> WebSocket:
            ws_connection_context = service_provider.get(IWebSocketConnectionHost)  # type: ignore
            return ws_connection_context.get_client()

        websocket_context = CallableProvider(get_websocket_connection)
        service_provider.register(WebSocket, websocket_context)
        service_provider.register(StarletteWebSocket, websocket_context)

    async def __call__(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        if scope["type"] not in ["http", "websocket"]:  # pragma: no cover
            await super().__call__(scope, receive, send)
            return

        scope[SCOPE_RESPONSE_STARTED] = False

        async def sender(message: TMessage) -> None:
            if message["type"] == "http.response.start":
                scope[SCOPE_RESPONSE_STARTED] = True
            await send(message)

        async with self.injector.create_request_service_provider() as service_provider:
            host_context = HostContext(scope=scope, receive=receive, send=sender)
            service_provider.update_context(t.cast(t.Type, IHostContext), host_context)
            service_provider.update_context(t.cast(t.Type, HostContext), host_context)

            service_provider.register_scoped(
                IHTTPConnectionHost,
                CallableProvider(HTTPConnectionContextFactory(host_context)),
            )

            service_provider.register_scoped(
                IWebSocketConnectionHost,
                CallableProvider(WebSocketContextFactory(host_context)),
            )

            self._register_request(service_provider)
            self._register_websocket(service_provider)
            self._register_response(service_provider)
            self._register_connection(service_provider)

            scope[SCOPE_SERVICE_PROVIDER] = service_provider
            scope[SCOPE_HOST_CONTEXT_PROVIDER] = host_context

            if host_context.get_type() == "http":
                await super().__call__(scope, receive, sender)
            else:
                await self.app(scope, receive, sender)

    async def error_handler(self, request: Request, exc: Exception) -> Response:
        host_context = request.scope[SCOPE_HOST_CONTEXT_PROVIDER]
        assert self._500_error_handler
        response = await self._500_error_handler.catch(host_context, exc)
        return response

    def error_response(self, request: StarletteRequest, exc: Exception) -> Response:
        return JSONResponse(
            dict(detail="Internal server error", status_code=500), status_code=500
        )
