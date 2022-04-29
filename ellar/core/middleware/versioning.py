import typing as t

from ellar.constants import SCOPE_API_VERSIONING_RESOLVER
from ellar.core.versioning import BaseAPIVersioning
from ellar.types import TReceive, TScope, TSend

if t.TYPE_CHECKING:
    from ellar.core.conf import Config
    from ellar.core.main import ArchitekApp


class RequestVersioningMiddleware:
    def __init__(self, app: "ArchitekApp", *, debug: bool, config: "Config") -> None:
        self.app = app
        self.debug = debug
        self.config = config

    async def __call__(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await self.app(scope, receive, send)
            return

        if self.config.VERSIONING_SCHEME:
            scheme = t.cast(BaseAPIVersioning, self.config.VERSIONING_SCHEME)

            version_scheme_resolver = scheme.get_version_resolver(scope)
            version_scheme_resolver.resolve()
            scope[SCOPE_API_VERSIONING_RESOLVER] = version_scheme_resolver
        await self.app(scope, receive, send)
