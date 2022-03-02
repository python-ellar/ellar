import typing

from starletteapi.constants import SCOPE_SERVICE_PROVIDER
from starletteapi.types import TScope, TReceive, TSend, ASGIApp

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

        scope[SCOPE_SERVICE_PROVIDER] = self.injector.create_di_request_service_provider(context={})
        await self.app(scope, receive, send)
