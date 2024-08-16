import typing as t

from ellar.common.constants import EXCEPTION_HANDLERS_KEY, MODULE_DECORATOR_ITEM
from ellar.pydantic import BaseModel


class ValidateExceptionHandler(BaseModel):
    key: t.Union[int, t.Type[Exception]]
    value: t.Union[t.Callable, t.Type]


def _add_exception_handler(
    exc_class_or_status_code: t.Union[int, t.Type[Exception]],
    handler: t.Union[t.Callable, t.Type],
    app: bool = False,
) -> None:
    validator = ValidateExceptionHandler(key=exc_class_or_status_code, value=handler)
    exception_handlers = {validator.key: (validator.value, app)}
    setattr(handler, EXCEPTION_HANDLERS_KEY, exception_handlers)
    setattr(handler, MODULE_DECORATOR_ITEM, EXCEPTION_HANDLERS_KEY)


def exception_handler(
    exc_or_status_code: t.Union[int, t.Type[Exception]], app: bool = False
) -> t.Callable:
    """
    ========= MODULE DECORATOR ==============

    Defines Exception Handler at Module Level
    :param exc_or_status_code: Exception Class or Status Code
    :param app: Indicates Exception Handler will be global to the application
    :return: Function
    """

    def decorator(func: t.Union[t.Callable, t.Type]) -> t.Callable:
        _add_exception_handler(exc_or_status_code, func, app)
        return func

    return decorator
