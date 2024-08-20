from starlette.middleware.gzip import GZipMiddleware as GZipMiddleware
from starlette.middleware.httpsredirect import (
    HTTPSRedirectMiddleware as HTTPSRedirectMiddleware,
)
from starlette.middleware.wsgi import WSGIMiddleware as WSGIMiddleware

from .cors import CORSMiddleware
from .errors import ServerErrorMiddleware
from .exceptions import ExceptionMiddleware
from .function import FunctionBasedMiddleware, as_middleware
from .middleware import EllarMiddleware as Middleware
from .trusted_host import TrustedHostMiddleware
from .versioning import RequestVersioningMiddleware

__all__ = [
    "Middleware",
    "FunctionBasedMiddleware",
    "CORSMiddleware",
    "ServerErrorMiddleware",
    "ExceptionMiddleware",
    "GZipMiddleware",
    "HTTPSRedirectMiddleware",
    "TrustedHostMiddleware",
    "WSGIMiddleware",
    "RequestVersioningMiddleware",
    "ServerErrorMiddleware",
    "as_middleware",
]
