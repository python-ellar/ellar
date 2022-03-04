import typing

from injector import CallableProvider

from starletteapi.constants import SCOPE_SERVICE_PROVIDER
from starletteapi.context import ExecutionContext
from starletteapi.requests import HTTPConnection, Request
from starletteapi.responses import Response
from starletteapi.types import TScope, TReceive, TSend, ASGIApp
from starletteapi.websockets import WebSocket

if typing.TYPE_CHECKING:
    from starletteapi.main import StarletteApp
    from starletteapi.di.injector import StarletteInjector


class DIRequestServiceProviderMiddleware:
    def __init__(self, app: ASGIApp, *, debug: bool, injector: 'StarletteInjector') -> None:
        self.app = app
        self.debug = debug
        self.injector = injector

    async def __call__(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await self.app(scope, receive, send)
            return

        di_request_service_provider = self.injector.create_di_request_service_provider(context={})
        execute_context = ExecutionContext(scope=scope, receive=receive, send=send)
        di_request_service_provider.update_context(ExecutionContext, execute_context)

        di_request_service_provider.update_context(
            HTTPConnection, CallableProvider(execute_context.switch_to_http_connection)
        )
        di_request_service_provider.update_context(
            WebSocket, CallableProvider(execute_context.switch_to_websocket)
        )
        di_request_service_provider.update_context(
            Request, CallableProvider(execute_context.switch_to_request)
        )
        di_request_service_provider.update_context(
            Response, CallableProvider(execute_context.get_response)
        )
        scope[SCOPE_SERVICE_PROVIDER] = di_request_service_provider
        await self.app(scope, receive, send)
