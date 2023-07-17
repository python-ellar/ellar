from abc import ABC

from ellar.auth.handlers.schemes import HttpBasicAuth, HttpBearerAuth, HttpDigestAuth
from ellar.common import APIException

from .mixin import GuardAuthMixin


class GuardHttpBearerAuth(GuardAuthMixin, HttpBearerAuth, ABC):
    exception_class = APIException


class GuardHttpBasicAuth(GuardAuthMixin, HttpBasicAuth, ABC):
    exception_class = APIException


class GuardHttpDigestAuth(GuardAuthMixin, HttpDigestAuth, ABC):
    exception_class = APIException
