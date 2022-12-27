import typing as t

from pydantic import BaseModel

from ellar.constants import EXCEPTION_HANDLERS_KEY


class ValidateExceptionHandler(BaseModel):
    key: t.Union[int, t.Type[Exception]]
    value: t.Union[t.Callable, t.Type]


def _add_exception_handler(
    exc_class_or_status_code: t.Union[int, t.Type[Exception]],
    handler: t.Union[t.Callable, t.Type],
) -> None:
    validator = ValidateExceptionHandler(key=exc_class_or_status_code, value=handler)
    exception_handlers = {validator.key: validator.value}
    setattr(handler, EXCEPTION_HANDLERS_KEY, exception_handlers)


def exception_handler(
    exc_class_or_status_code: t.Union[int, t.Type[Exception]]
) -> t.Callable:
    """
    ========= MODULE DECORATOR ==============

    Defines Exception Handler at Module Level
    :param exc_class_or_status_code:
    :return: Function
    """

    def decorator(func: t.Union[t.Callable, t.Type]) -> t.Callable:
        _add_exception_handler(exc_class_or_status_code, func)
        return func

    return decorator
