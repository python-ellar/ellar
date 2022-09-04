from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware


class Config:
    MIDDLEWARE = [
        Middleware(TrustedHostMiddleware, allowed_hosts=["testserver", "*.example.org"])
    ]
