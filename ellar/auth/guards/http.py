from abc import ABC

from ellar.common import APIException

from ..handlers.schemes import HttpBasicAuth, HttpBearerAuth, HttpDigestAuth
from .mixin import GuardAuthMixin


class GuardHttpBearerAuth(GuardAuthMixin, HttpBearerAuth, ABC):
    exception_class = APIException


class GuardHttpBasicAuth(GuardAuthMixin, HttpBasicAuth, ABC):
    exception_class = APIException


class GuardHttpDigestAuth(GuardAuthMixin, HttpDigestAuth, ABC):
    exception_class = APIException
