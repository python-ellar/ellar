from ellar.di import injectable

from .auth_handler import AuthenticationHandlerType
from .interfaces import IAuthConfig, IIdentityProvider


@injectable
class BaseIdentityProvider(IIdentityProvider):
    """
    User should inherit from `BaseAuthenticationShieldConfiguration`
    and override `configure_authentication` to configure Authentication Schemes
    and configure_authorization to configure Authorization policies
    """

    __slots__ = ("auth_config",)

    def __init__(self, auth_config: IAuthConfig) -> None:
        self.auth_config = auth_config

    def add_authentication(self, authentication: AuthenticationHandlerType) -> None:
        self.auth_config.add_authentication(authentication)

    def configure(self) -> None:
        """Do Nothing"""
