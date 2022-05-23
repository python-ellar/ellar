import typing as t

from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

from ellar.core.schema import Schema


class MiddlewareSchema(Schema):
    middleware_class: t.Type[BaseHTTPMiddleware]
    dispatch: t.Callable[[t.Any, t.Callable], t.Any]
    options: t.Dict

    def create_middleware(self) -> Middleware:
        return Middleware(self.middleware_class, dispatch=self.dispatch, **self.options)
