import typing

from injector import CallableProvider

from architek.constants import SCOPE_SERVICE_PROVIDER
from architek.context import ExecutionContext
from architek.requests import HTTPConnection, Request
from architek.response import Response
from architek.types import ASGIApp, TReceive, TScope, TSend
from architek.websockets import WebSocket

if typing.TYPE_CHECKING:
    from architek.di.injector import StarletteInjector


class RequestServiceProviderMiddleware:
    def __init__(
        self, app: ASGIApp, *, debug: bool, injector: "StarletteInjector"
    ) -> None:
        self.app = app
        self.debug = debug
        self.injector = injector

    async def __call__(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await self.app(scope, receive, send)
            return

        di_request_service_provider = self.injector.create_request_service_provider()
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
        with di_request_service_provider:
            await self.app(scope, receive, send)
