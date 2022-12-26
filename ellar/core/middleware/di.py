import typing as t

from injector import CallableProvider
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.requests import (
    HTTPConnection as StarletteHTTPConnection,
    Request as StarletteRequest,
)
from starlette.websockets import WebSocket as StarletteWebSocket

from ellar.constants import SCOPE_EXECUTION_CONTEXT_PROVIDER, SCOPE_SERVICE_PROVIDER
from ellar.core.connection.http import HTTPConnection, Request
from ellar.core.connection.websocket import WebSocket
from ellar.core.context import ExecutionContext, IExecutionContext
from ellar.core.response import Response
from ellar.types import ASGIApp, TReceive, TScope, TSend

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
    def _register_connection(
        cls, ctx: ExecutionContext, request_provider: "RequestServiceProvider"
    ) -> None:
        request_provider.update_context(
            HTTPConnection,
            CallableProvider(ctx.switch_to_http_connection),
        )
        request_provider.update_context(
            StarletteHTTPConnection,
            CallableProvider(ctx.switch_to_http_connection),
        )

    @classmethod
    def _register_request(
        cls, ctx: ExecutionContext, request_provider: "RequestServiceProvider"
    ) -> None:
        request_provider.update_context(
            Request, CallableProvider(ctx.switch_to_request)
        )
        request_provider.update_context(
            StarletteRequest, CallableProvider(ctx.switch_to_request)
        )

    @classmethod
    def _register_response(
        cls, ctx: ExecutionContext, request_provider: "RequestServiceProvider"
    ) -> None:
        request_provider.update_context(Response, CallableProvider(ctx.get_response))

    @classmethod
    def _register_websocket(
        cls, ctx: ExecutionContext, request_provider: "RequestServiceProvider"
    ) -> None:
        request_provider.update_context(
            WebSocket, CallableProvider(ctx.switch_to_websocket)
        )
        request_provider.update_context(
            StarletteWebSocket, CallableProvider(ctx.switch_to_websocket)
        )

    async def __call__(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        if scope["type"] not in ["http", "websocket"]:  # pragma: no cover
            await super().__call__(scope, receive, send)
            return

        async with self.injector.create_request_service_provider() as request_provider:
            execute_context = ExecutionContext(scope=scope, receive=receive, send=send)
            request_provider.update_context(
                t.cast(t.Type, IExecutionContext), execute_context
            )
            request_provider.update_context(
                t.cast(t.Type, ExecutionContext), execute_context
            )

            self._register_request(execute_context, request_provider)
            self._register_websocket(execute_context, request_provider)
            self._register_response(execute_context, request_provider)
            self._register_connection(execute_context, request_provider)

            scope[SCOPE_SERVICE_PROVIDER] = request_provider
            scope[SCOPE_EXECUTION_CONTEXT_PROVIDER] = execute_context
            if scope["type"] == "http":
                await super().__call__(scope, receive, send)
            else:
                await self.app(scope, receive, send)

    async def error_handler(self, request: Request, exc: Exception) -> Response:
        execute_context = request.scope[SCOPE_EXECUTION_CONTEXT_PROVIDER]
        assert self._500_error_handler
        response = await self._500_error_handler.catch(ctx=execute_context, exc=exc)
        return response
