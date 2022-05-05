import typing as t

from starlette.middleware.base import BaseHTTPMiddleware

from ellar.constants import MIDDLEWARE_HANDLERS_KEY
from ellar.core.middleware.schema import MiddlewareSchema


def add_middleware(
    middleware_class: type, dispatch: t.Callable, **options: t.Any
) -> None:
    setattr(
        dispatch,
        MIDDLEWARE_HANDLERS_KEY,
        MiddlewareSchema(
            middleware_class=middleware_class, dispatch=dispatch, options=options
        ),
    )


def middleware(middleware_type: str) -> t.Callable:
    assert middleware_type == "http", 'Currently only middleware("http") is supported.'

    def decorator(func: t.Callable) -> t.Callable:
        add_middleware(BaseHTTPMiddleware, dispatch=func)
        return func

    return decorator
