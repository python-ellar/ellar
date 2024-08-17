from ellar.common.types import ASGIApp
from ellar.core.conf import Config
from starlette.middleware.trustedhost import (
    TrustedHostMiddleware as BaseTrustedHostMiddleware,
)

from .middleware import EllarMiddleware


class TrustedHostMiddleware(BaseTrustedHostMiddleware):
    def __init__(self, app: ASGIApp, config: Config) -> None:
        self.config = config

        allowed_hosts = config.ALLOWED_HOSTS

        if config.DEBUG and allowed_hosts != ["*"]:
            allowed_hosts = ["*"]

        super().__init__(
            app, allowed_hosts=allowed_hosts, www_redirect=self.config.REDIRECT_HOST
        )


# TrustedHostMiddleware Configuration
trusted_host_middleware = EllarMiddleware(TrustedHostMiddleware)
