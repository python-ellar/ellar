from starlette.middleware import Middleware as Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
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
from .exceptions import ExceptionMiddleware
from .function import FunctionBasedMiddleware
from .versioning import RequestVersioningMiddleware

__all__ = [
    "Middleware",
    "AuthenticationMiddleware",
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
]
