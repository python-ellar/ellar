import typing as t

from pydantic import BaseModel

from ellar.constants import EXCEPTION_HANDLERS_KEY


class ValidateExceptionHandler(BaseModel):
    key: t.Union[int, t.Type[Exception]]
    value: t.Callable


def add_exception_handler(
    exc_class_or_status_code: t.Union[int, t.Type[Exception]],
    handler: t.Callable,
) -> None:
    validator = ValidateExceptionHandler(key=exc_class_or_status_code, value=handler)
    exception_handlers = {validator.key: validator.value}
    setattr(handler, EXCEPTION_HANDLERS_KEY, exception_handlers)


def exception_handler(
    exc_class_or_status_code: t.Union[int, t.Type[Exception]]
) -> t.Callable:
    def decorator(func: t.Callable) -> t.Callable:
        add_exception_handler(exc_class_or_status_code, func)
        return func

    return decorator
