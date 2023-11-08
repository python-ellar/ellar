from abc import ABC

from ellar.common import APIException

from ..handlers.schemes import APIKeyCookie, APIKeyHeader, APIKeyQuery
from .mixin import GuardAuthMixin


class GuardAPIKeyQuery(APIKeyQuery, GuardAuthMixin, ABC):
    openapi_in: str = "query"
    exception_class = APIException


class GuardAPIKeyCookie(APIKeyCookie, GuardAuthMixin, ABC):
    openapi_in: str = "cookie"
    exception_class = APIException


class GuardAPIKeyHeader(APIKeyHeader, GuardAuthMixin, ABC):
    openapi_in: str = "header"
    exception_class = APIException
