import typing as t

from ellar.common.interfaces import IExceptionHandler, IHostContext
from ellar.common.utils import is_async_callable
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response


class CallableExceptionHandler(IExceptionHandler):
    """
    Default Exception Handler Setup for functions

    usage:

    ```python

    class CustomException(Exception):
        pass


    def exception_handler_fun(ctx: IExecutionContext, exc: Exception):
        return PlainTextResponse('Bad Request', status_code=400)

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
        callable_exception_handler: t.Union[
            t.Callable[
                [IHostContext, Exception],
                t.Union[t.Awaitable[Response], Response, t.Any],
            ],
            t.Any,
        ],
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
        self, ctx: IHostContext, exc: Exception
    ) -> t.Union[Response, t.Any]:
        args = tuple(list(self.func_args) + [ctx, exc])
        if self.is_async:
            return await self.callable_exception_handler(*args)  # type:ignore
        return await run_in_threadpool(self.callable_exception_handler, *args)

    def __eq__(self, other: t.Any) -> bool:
        if isinstance(other, CallableExceptionHandler):
            return (
                other.exception_type_or_code == self.exception_type_or_code
                and other.callable_exception_handler == other.callable_exception_handler
            )
        return False
