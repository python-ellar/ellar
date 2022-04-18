import typing as t

from starlette.requests import (
    HTTPConnection as StarletteHTTPConnection,
    Request as StarletteRequest,
)

from architek.constants import SCOPE_SERVICE_PROVIDER

if t.TYPE_CHECKING:
    from architek.di.injector import RequestServiceProvider


class HTTPConnection(StarletteHTTPConnection):
    @property
    def service_provider(self) -> "RequestServiceProvider":
        assert (
            SCOPE_SERVICE_PROVIDER in self.scope
        ), "DIRequestServiceProviderMiddleware must be installed to access request.service_provider"
        return t.cast("RequestServiceProvider", self.scope[SCOPE_SERVICE_PROVIDER])


class Request(StarletteRequest, HTTPConnection):
    pass
