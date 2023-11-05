import typing as t

from ellar.common import Identity
from ellar.common.constants import SCOPE_SERVICE_PROVIDER
from starlette.requests import (
    HTTPConnection as StarletteHTTPConnection,
)
from starlette.requests import (
    Request as StarletteRequest,
)

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.di import EllarInjector


class HTTPConnection(StarletteHTTPConnection):
    @property
    def service_provider(self) -> "EllarInjector":
        assert (
            SCOPE_SERVICE_PROVIDER in self.scope
        ), "RequestServiceProviderMiddleware must be installed to access request.service_provider"
        return t.cast("EllarInjector", self.scope[SCOPE_SERVICE_PROVIDER])

    @property
    def user(self) -> Identity:
        return t.cast(Identity, self.scope["user"])


class Request(StarletteRequest, HTTPConnection):
    pass
