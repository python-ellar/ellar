import typing as t

from ellar.common.compatible import AttributeDict
from ellar.common.constants import MIDDLEWARE_HANDLERS_KEY, MODULE_DECORATOR_ITEM


def _add_middleware(dispatch: t.Callable, app: bool = False, **options: t.Any) -> None:
    setattr(
        dispatch,
        MIDDLEWARE_HANDLERS_KEY,
        AttributeDict(dispatch=dispatch, options=options, is_global=app),
    )
    setattr(dispatch, MODULE_DECORATOR_ITEM, MIDDLEWARE_HANDLERS_KEY)


def middleware(app: bool = False) -> t.Callable:
    """
    ========= MODULE DECORATOR ==============

    Defines middleware functions at  @Module decorated class level

    Usage:

    @middleware()
    async def my_middleware(cls, context: IExecutionContext, call_next):
        print("Called my_middleware")
        request = context.switch_to_http_connection().get_request()
        request.state.my_middleware = True
        await call_next()

    :return: Function
    """

    def decorator(func: t.Callable) -> t.Callable:
        _add_middleware(dispatch=func, app=app)
        return func

    return decorator
