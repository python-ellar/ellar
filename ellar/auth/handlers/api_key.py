import typing as t
from abc import ABC

from .base import BaseAPIKeyAuthenticationHandler

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core import HTTPConnection


class QueryAPIKeyAuthenticationHandler(BaseAPIKeyAuthenticationHandler, ABC):
    parameter_name: str = "key"
    openapi_in: str = "query"

    def _get_key(self, connection: "HTTPConnection") -> t.Optional[t.Any]:
        return connection.query_params.get(self.parameter_name)


class CookieAPIKeyAuthenticationHandler(BaseAPIKeyAuthenticationHandler, ABC):
    parameter_name: str = "key"
    openapi_in: str = "query"

    def _get_key(self, connection: "HTTPConnection") -> t.Optional[t.Any]:
        return connection.cookies.get(self.parameter_name)


class HeaderAPIKeyAuthenticationHandler(BaseAPIKeyAuthenticationHandler, ABC):
    parameter_name: str = "key"
    openapi_in: str = "query"

    def _get_key(self, connection: "HTTPConnection") -> t.Optional[t.Any]:
        return connection.headers.get(self.parameter_name)
