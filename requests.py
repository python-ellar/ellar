import typing
from starlette.requests import HTTPConnection as StarletteHTTPConnection, Request as StarletteRequest # noqa

from starletteapi.constants import SCOPE_SERVICE_PROVIDER

if typing.TYPE_CHECKING:
    from starletteapi.di.injector import DIRequestServiceProvider


class HTTPConnection(StarletteHTTPConnection):
    @property
    def service_provider(self) -> 'DIRequestServiceProvider':
        assert (
                SCOPE_SERVICE_PROVIDER in self.scope
        ), "DIRequestServiceProviderMiddleware must be installed to access request.service_provider"
        return self.scope[SCOPE_SERVICE_PROVIDER]


class Request(StarletteRequest, StarletteHTTPConnection):
    pass
