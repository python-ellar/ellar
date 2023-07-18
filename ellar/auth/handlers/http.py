from abc import ABC

from .mixin import BaseAuthenticationHandlerMixin
from .model import BaseAuthenticationHandler
from .schemes import HttpBasicAuth, HttpBearerAuth


class HttpBearerAuthenticationHandler(
    BaseAuthenticationHandlerMixin, HttpBearerAuth, BaseAuthenticationHandler, ABC
):
    scheme: str = "bearer"


class HttpBasicAuthenticationHandler(
    BaseAuthenticationHandlerMixin, HttpBasicAuth, BaseAuthenticationHandler, ABC
):
    scheme: str = "basic"
