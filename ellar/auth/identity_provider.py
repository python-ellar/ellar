from ellar.di import injectable

from .handlers import AuthenticationHandlerType
from .interfaces import IAuthConfig, IIdentitySchemeProvider


@injectable
class BaseIdentitySchemeProvider(IIdentitySchemeProvider):
    """
    User should inherit from `BaseIdentityProvider`
    and override `configure` to configure Authentication Schemes
    """

    __slots__ = ("auth_config",)

    def __init__(self, auth_config: IAuthConfig) -> None:
        self.auth_config = auth_config

    def add_authentication(self, authentication: AuthenticationHandlerType) -> None:
        self.auth_config.add_authentication(authentication)

    def configure(self) -> None:
        """Do Nothing"""
