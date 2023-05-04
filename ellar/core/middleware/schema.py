import typing as t

from starlette.middleware import Middleware

from ellar.core.serializer import Serializer

from .function import FunctionBasedMiddleware


class MiddlewareSchema(Serializer):
    middleware_class: t.Type[FunctionBasedMiddleware]
    dispatch: t.Callable[[t.Any, t.Callable], t.Any]
    options: t.Dict

    def create_middleware(self) -> Middleware:
        return Middleware(self.middleware_class, dispatch=self.dispatch, **self.options)
