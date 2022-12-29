import typing as t

from ellar.di import injectable

from .handlers import (
    APIExceptionHandler,
    HTTPExceptionHandler,
    RequestValidationErrorHandler,
    WebSocketExceptionHandler,
)
from .interfaces import IExceptionHandler, IExceptionMiddlewareService


@injectable()
class ExceptionMiddlewareService(IExceptionMiddlewareService):
    DEFAULTS: t.List[IExceptionHandler] = [
        HTTPExceptionHandler(),
        APIExceptionHandler(),
        WebSocketExceptionHandler(),
        RequestValidationErrorHandler(),
    ]

    def __init__(self) -> None:
        self._status_handlers: t.Dict[int, IExceptionHandler] = {}
        self._exception_handlers: t.Dict[t.Type[Exception], IExceptionHandler] = {}
        self._500_error_handler: t.Optional[IExceptionHandler] = None

    def build_exception_handlers(self, *exception_handlers: IExceptionHandler) -> None:
        handlers = list(self.DEFAULTS) + list(exception_handlers)
        for key, value in handlers:
            if key == 500:
                self._500_error_handler = value
                continue
            self._add_exception_handler(key, value)

    def get_500_error_handler(
        self,
    ) -> t.Optional[IExceptionHandler]:
        return self._500_error_handler

    def _add_exception_handler(
        self,
        exc_class_or_status_code: t.Union[int, t.Type[Exception]],
        handler: IExceptionHandler,
    ) -> None:
        if isinstance(exc_class_or_status_code, int):
            assert isinstance(handler, IExceptionHandler)
            self._status_handlers[exc_class_or_status_code] = handler
        else:
            assert issubclass(exc_class_or_status_code, Exception)
            assert isinstance(handler, IExceptionHandler)
            self._exception_handlers[exc_class_or_status_code] = handler

    def lookup_exception_handler(self, exc: Exception) -> t.Optional[IExceptionHandler]:
        for cls in type(exc).__mro__:
            if cls in self._exception_handlers:
                return self._exception_handlers[cls]
        return None

    def lookup_status_code_exception_handler(
        self, status_code: int
    ) -> t.Optional[IExceptionHandler]:
        return self._status_handlers.get(status_code)
