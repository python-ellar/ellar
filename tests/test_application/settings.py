from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

MIDDLEWARE = [
    Middleware(TrustedHostMiddleware, allowed_hosts=["testserver", "*.example.org"])
]
