import typing as t

from ellar.di import injectable

from ..interfaces import IAuthConfig, IAuthorizationConfig, IIdentityProvider
from .auth_handler import AuthenticationHandlerType

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.auth.policy import Policy


@injectable
class BaseIdentityProvider(IIdentityProvider):
    """
    User should inherit from `BaseAuthenticationShieldConfiguration`
    and override `configure_authentication` to configure Authentication Schemes
    and configure_authorization to configure Authorization policies
    """

    __slots__ = ("auth_config", "authorization_config")

    def __init__(
        self, auth_config: IAuthConfig, authorization_config: IAuthorizationConfig
    ) -> None:
        self.auth_config = auth_config
        self.authorization_config = authorization_config

    def add_authentication(self, authentication: AuthenticationHandlerType) -> None:
        self.auth_config.add_authentication(authentication)

    def add_authorization(self, name: str, policy: "Policy") -> None:
        self.authorization_config.add_authorization(name, policy)

    async def configure(self) -> None:
        """Do Nothing"""
