import typing as t
from abc import ABC

from .base import BaseAPIKey

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.connection import HTTPConnection


class APIKeyQuery(BaseAPIKey, ABC):
    openapi_in: str = "query"

    def _get_key(self, connection: "HTTPConnection") -> t.Optional[t.Any]:
        return connection.query_params.get(self.parameter_name)


class APIKeyCookie(BaseAPIKey, ABC):
    openapi_in: str = "cookie"

    def _get_key(self, connection: "HTTPConnection") -> t.Optional[t.Any]:
        return connection.cookies.get(self.parameter_name)


class APIKeyHeader(BaseAPIKey, ABC):
    openapi_in: str = "header"

    def _get_key(self, connection: "HTTPConnection") -> t.Optional[t.Any]:
        return connection.headers.get(self.parameter_name)
