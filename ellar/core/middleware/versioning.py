import typing as t

from ellar.common.constants import SCOPE_API_VERSIONING_RESOLVER
from ellar.common.types import TReceive, TScope, TSend
from ellar.core.conf import Config
from ellar.core.versioning import BaseAPIVersioning, DefaultAPIVersioning
from starlette.types import ASGIApp

from .middleware import EllarMiddleware


class RequestVersioningMiddleware:
    def __init__(self, app: ASGIApp, config: "Config") -> None:
        self.app = app
        self.config = config

    async def __call__(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        if scope["type"] not in ["http", "websocket"]:  # pragma: no cover
            await self.app(scope, receive, send)
            return

        ## setup Versioning Resolvers
        scheme = (
            t.cast(BaseAPIVersioning, self.config.VERSIONING_SCHEME)
            or DefaultAPIVersioning()
        )

        version_scheme_resolver = scheme.get_version_resolver(scope)
        version_scheme_resolver.resolve()

        scope[SCOPE_API_VERSIONING_RESOLVER] = version_scheme_resolver
        await self.app(scope, receive, send)


# RequestVersioningMiddleware Configuration
versioning_middleware = EllarMiddleware(RequestVersioningMiddleware)
