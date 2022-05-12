import typing as t

from injector import CallableProvider
from starlette.middleware.errors import ServerErrorMiddleware

from ellar.constants import SCOPE_SERVICE_PROVIDER
from ellar.core.connection import HTTPConnection, Request, WebSocket
from ellar.core.context import ExecutionContext, IExecutionContext
from ellar.core.response import Response
from ellar.types import ASGIApp, TReceive, TScope, TSend

if t.TYPE_CHECKING:
    from ellar.di.injector import StarletteInjector


class RequestServiceProviderMiddleware(ServerErrorMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        *,
        debug: bool,
        injector: "StarletteInjector",
        handler: t.Callable = None
    ) -> None:
        super(RequestServiceProviderMiddleware, self).__init__(
            debug=debug, handler=handler, app=app
        )
        self.injector = injector

    async def __call__(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await super().__call__(scope, receive, send)
            return

        async with self.injector.create_request_service_provider() as request_provider:
            execute_context = ExecutionContext(scope=scope, receive=receive, send=send)
            request_provider.update_context(
                t.cast(t.Type, IExecutionContext), execute_context
            )

            request_provider.update_context(
                HTTPConnection,
                CallableProvider(execute_context.switch_to_http_connection),
            )
            request_provider.update_context(
                WebSocket, CallableProvider(execute_context.switch_to_websocket)
            )
            request_provider.update_context(
                Request, CallableProvider(execute_context.switch_to_request)
            )
            request_provider.update_context(
                Response, CallableProvider(execute_context.get_response)
            )
            scope[SCOPE_SERVICE_PROVIDER] = request_provider
            await super().__call__(scope, receive, send)
