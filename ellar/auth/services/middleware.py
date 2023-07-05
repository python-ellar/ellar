from functools import partial

from ellar.common import AnonymousIdentity, Identity, IHostContext
from ellar.di import injectable

from ..handlers import AuthenticationHandlerType, BaseAuthenticationHandler
from ..interfaces import IAuthConfig, IIdentitySchemeProvider


@injectable
class IdentityAuthenticationService:
    def __init__(
        self,
        identity_scheme_provider: IIdentitySchemeProvider,
        auth_config: IAuthConfig,
    ) -> None:
        self.identity_scheme_provider = identity_scheme_provider
        self.auth_config = auth_config
        self._configure = False

    async def setup_auth_services(self) -> None:
        if not self._configure:
            self.identity_scheme_provider.configure()
            self._configure = True

    def _get_authentication_handler_object(
        self, context: IHostContext, auth_handler: AuthenticationHandlerType
    ) -> BaseAuthenticationHandler:
        if isinstance(auth_handler, type):
            return context.get_service_provider().get(auth_handler)  # type: ignore[no-any-return]
        return auth_handler

    async def authenticate(self, context: IHostContext) -> None:
        context.user = await self._authenticate_action(context)

    # async def _detect_authentication_scheme(self, context: IHostContext) -> str:
    #     pass

    async def _authenticate_action(self, context: IHostContext) -> Identity:
        partial_get_authentication_handler_object = partial(
            self._get_authentication_handler_object, context
        )
        for authentication_scheme in map(
            partial_get_authentication_handler_object,
            self.auth_config.get_authentication_schemes(),
        ):
            identify = await authentication_scheme.authenticate(context)

            if identify:
                return identify

        return AnonymousIdentity()
