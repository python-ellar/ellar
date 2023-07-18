from abc import ABC

from .mixin import BaseAuthenticationHandlerMixin
from .model import BaseAuthenticationHandler
from .schemes import APIKeyCookie, APIKeyHeader, APIKeyQuery


class QueryAPIKeyAuthenticationHandler(
    BaseAuthenticationHandlerMixin, APIKeyQuery, BaseAuthenticationHandler, ABC
):
    scheme: str = "query"


class CookieAPIKeyAuthenticationHandler(
    BaseAuthenticationHandlerMixin, APIKeyCookie, BaseAuthenticationHandler, ABC
):
    scheme: str = "cookie"


class HeaderAPIKeyAuthenticationHandler(
    BaseAuthenticationHandlerMixin, APIKeyHeader, BaseAuthenticationHandler, ABC
):
    scheme: str = "header"
