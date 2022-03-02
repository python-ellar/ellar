import typing

from starletteapi.constants import SCOPE_API_VERSIONING_RESOLVER
from starletteapi.types import TScope, TReceive, TSend
from starletteapi.versioning import DefaultAPIVersioning

if typing.TYPE_CHECKING:
    from starletteapi.main import StarletteApp
    from starletteapi.conf import Config


class RequestVersioningMiddleware:
    def __init__(self, app: 'StarletteApp', *, debug: bool, config: 'Config') -> None:
        self.app = app
        self.debug = debug
        self.config = config

    async def __call__(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await self.app(scope, receive, send)
            return

        scheme = self.config.VERSIONING_SCHEME or DefaultAPIVersioning()
        if isinstance(scheme, type):
            scheme = scheme()
        # await scheme.resolve(scope)
        version_scheme_resolver = scheme.get_version_resolver(scope)
        version_scheme_resolver.resolve()
        scope[SCOPE_API_VERSIONING_RESOLVER] = version_scheme_resolver
        await self.app(scope, receive, send)
