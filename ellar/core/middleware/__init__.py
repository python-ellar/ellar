import sys

from starlette.middleware import Middleware as Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
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

from .di import RequestServiceProviderMiddleware
from .versioning import RequestVersioningMiddleware

if sys.version_info >= (3, 7):  # pragma: no cover
    from starlette.middleware.exceptions import ExceptionMiddleware
else:
    from starlette.exceptions import ExceptionMiddleware  # type: ignore


__all__ = [
    "Middleware",
    "AuthenticationMiddleware",
    "BaseHTTPMiddleware",
    "CORSMiddleware",
    "ServerErrorMiddleware",
    "ExceptionMiddleware",
    "GZipMiddleware",
    "HTTPSRedirectMiddleware",
    "TrustedHostMiddleware",
    "WSGIMiddleware",
    "RequestVersioningMiddleware",
    "RequestServiceProviderMiddleware",
]
