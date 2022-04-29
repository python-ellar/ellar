import typing as t

from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

from architek.constants import MIDDLEWARE_HANDLERS_KEY
from architek.core import Config


def add_middleware(middleware_class: type, **options: t.Any) -> None:
    user_middleware = Config.get_value(MIDDLEWARE_HANDLERS_KEY) or []
    if not isinstance(user_middleware, list):
        user_middleware = []
    user_middleware.insert(0, Middleware(middleware_class, **options))
    Config.add_value(**{MIDDLEWARE_HANDLERS_KEY: user_middleware})


def middleware(middleware_type: str) -> t.Callable:
    assert middleware_type == "http", 'Currently only middleware("http") is supported.'

    def decorator(func: t.Callable) -> t.Callable:
        add_middleware(BaseHTTPMiddleware, dispatch=func)
        return func

    return decorator
