import typing as t

from ellar.constants import MIDDLEWARE_HANDLERS_KEY
from ellar.core.middleware import FunctionBasedMiddleware
from ellar.core.middleware.schema import MiddlewareSchema


def _add_middleware(
    middleware_class: type, dispatch: t.Callable, **options: t.Any
) -> None:
    setattr(
        dispatch,
        MIDDLEWARE_HANDLERS_KEY,
        MiddlewareSchema(
            middleware_class=middleware_class, dispatch=dispatch, options=options
        ),
    )


def middleware() -> t.Callable:
    """
    ========= MODULE DECORATOR ==============

    Defines middle functions at module level
    :return: Function
    """

    def decorator(func: t.Callable) -> t.Callable:
        _add_middleware(FunctionBasedMiddleware, dispatch=func)
        return func

    return decorator
