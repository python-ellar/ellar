import typing as t

from ellar.common.compatible import AttributeDict
from ellar.common.constants import MIDDLEWARE_HANDLERS_KEY


def _add_middleware(dispatch: t.Callable, **options: t.Any) -> None:
    setattr(
        dispatch,
        MIDDLEWARE_HANDLERS_KEY,
        AttributeDict(dispatch=dispatch, options=options),
    )


def middleware() -> t.Callable:
    """
    ========= MODULE DECORATOR ==============

    Defines middleware functions at  @Module decorated class level
    :return: Function
    """

    def decorator(func: t.Callable) -> t.Callable:
        _add_middleware(dispatch=func)
        return func

    return decorator
