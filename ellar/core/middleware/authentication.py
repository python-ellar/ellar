from starlette.routing import compile_path
from starlette.types import ASGIApp

from ellar.auth.services import IdentityMiddlewareService
from ellar.common import AnonymousIdentity, IHostContextFactory
from ellar.common.types import TReceive, TScope, TSend
from ellar.core.conf import Config
from ellar.di import EllarInjector


class IdentityMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        injector: EllarInjector,
        config: "Config",
        identity_service: IdentityMiddlewareService
    ) -> None:
        self.app = app
        self.identity_service = identity_service
        self.injector = injector
        self._configure = False

        path_regex, _, _ = compile_path(str(config.STATIC_MOUNT_PATH) + "/{path:path}")

        self._path_regex = path_regex

    async def __call__(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        if scope["type"] == "lifespan":
            await self.identity_service.setup_auth_shield_services()
            await self.app(scope, receive, send)
            return

        if not self.is_static(scope):
            context_factory = self.injector.get(IHostContextFactory)
            context = context_factory.create_context(scope, receive, send)

            context.user = AnonymousIdentity()
            await self.identity_service.authenticate(context)

        await self.app(scope, receive, send)

    def is_static(self, scope: TScope) -> bool:
        """
        Check is the request is for a static file
        """
        return self._path_regex.match(scope["path"]) is not None
