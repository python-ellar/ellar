import typing as t

from ellar.common import Identity
from ellar.core.context import current_injector
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
        return current_injector

    @property
    def user(self) -> Identity:
        return t.cast(Identity, self.scope["user"])


class Request(StarletteRequest, HTTPConnection):
    pass
