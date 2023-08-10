from starlette.middleware.cors import CORSMiddleware as CORSMiddleware
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.middleware.gzip import GZipMiddleware as GZipMiddleware
from starlette.middleware.httpsredirect import (
    HTTPSRedirectMiddleware as HTTPSRedirectMiddleware,
)
from starlette.middleware.trustedhost import (
    TrustedHostMiddleware as TrustedHostMiddleware,
)
from starlette.middleware.wsgi import WSGIMiddleware as WSGIMiddleware

from .authentication import IdentityMiddleware
from .di import RequestServiceProviderMiddleware
from .exceptions import ExceptionMiddleware
from .function import FunctionBasedMiddleware
from .middleware import EllarMiddleware as Middleware
from .sessions import SessionMiddleware
from .versioning import RequestVersioningMiddleware

__all__ = [
    "Middleware",
    "IdentityMiddleware",
    "FunctionBasedMiddleware",
    "CORSMiddleware",
    "ServerErrorMiddleware",
    "ExceptionMiddleware",
    "GZipMiddleware",
    "HTTPSRedirectMiddleware",
    "TrustedHostMiddleware",
    "WSGIMiddleware",
    "RequestVersioningMiddleware",
    "RequestServiceProviderMiddleware",
    "SessionMiddleware",
]
