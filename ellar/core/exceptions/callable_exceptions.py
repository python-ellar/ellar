import typing as t

from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from ellar.helper import is_async_callable

from ..context import IExecutionContext
from .interfaces import IExceptionHandler


class CallableExceptionHandler(IExceptionHandler):
    """
    Default Exception Handler Setup for functions

    usage:

    ```python

    class CustomException(Exception):
        pass


    def exception_handler_fun(ctx: IExecutionContext, exc: Exception):
        return PlainResponse('Bad Request', status_code=400)

    exception_400_handler = CallableExceptionHandler(
        exc_class_or_status_code=400, callable_exception_handler= exception_handler_fun
    )
    exception_custom_handler = CallableExceptionHandler(
        exc_class_or_status_code=CustomException, callable_exception_handler= exception_handler_fun
    )

    # in Config.py
    EXCEPTION_HANDLERS = [exception_handler, exception_custom_handler]

    ```
    """

    __slots__ = ("callable_exception_handler", "is_async", "func_args")
    exception_type_or_code: t.Union[t.Type[Exception], int] = 400

    def __init__(
        self,
        *func_args: t.Any,
        exc_class_or_status_code: t.Union[t.Type[Exception], int],
        callable_exception_handler: t.Callable[
            [IExecutionContext, Exception],
            t.Union[t.Awaitable[Response], Response, t.Any],
        ]
    ) -> None:
        self.callable_exception_handler = callable_exception_handler
        self.is_async = False
        self.func_args = func_args

        if not isinstance(exc_class_or_status_code, int):
            assert issubclass(exc_class_or_status_code, Exception)

        self.exception_type_or_code = exc_class_or_status_code

        if is_async_callable(callable_exception_handler):
            self.is_async = True

    async def catch(
        self, ctx: IExecutionContext, exc: Exception
    ) -> t.Union[Response, t.Any]:
        args = tuple(list(self.func_args) + [ctx, exc])
        if self.is_async:
            return await self.callable_exception_handler(*args)  # type:ignore
        return await run_in_threadpool(self.callable_exception_handler, *args)
