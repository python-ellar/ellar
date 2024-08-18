import typing as t

from ellar.common.interfaces import IExceptionHandler, IHostContext
from ellar.utils import is_async_callable
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
        exc_or_status_code: t.Union[t.Type[Exception], int],
        handler: t.Union[
            t.Callable[
                [IHostContext, Exception],
                t.Union[t.Awaitable[Response], Response, t.Any],
            ],
            t.Any,
        ],
    ) -> None:
        self.callable_exception_handler = handler
        self.is_async = False
        self.func_args = func_args

        if not isinstance(exc_or_status_code, int):
            assert issubclass(exc_or_status_code, Exception)

        self.exception_type_or_code = exc_or_status_code

        if is_async_callable(handler):
            self.is_async = True

    async def catch(
        self, ctx: IHostContext, exc: Exception
    ) -> t.Union[Response, t.Any]:
        args = tuple(list(self.func_args) + [ctx, exc])
        if self.is_async:
            return await self.callable_exception_handler(*args)  # type:ignore[misc]
        return await run_in_threadpool(self.callable_exception_handler, *args)  # type:ignore[arg-type]

    def __eq__(self, other: t.Any) -> bool:
        if isinstance(other, CallableExceptionHandler):
            return (
                other.exception_type_or_code == self.exception_type_or_code
                and other.callable_exception_handler == other.callable_exception_handler
            )
        return False


def as_exception_handler(
    exc_or_status_code: t.Union[t.Type[Exception], int],
) -> t.Callable[..., CallableExceptionHandler]:
    """
    Convert function to Functional ExceptionHandler ready to be used as an application exception handler
    :param exc_or_status_code: Exception Type or status code
    :return: CallableExceptionHandler

    eg:

    @as_exception_handler(404)
    async def error_404_handler(ctx: IExecutionContext, exc: HTTPException) -> Response:
        json_response_class = ctx.get_app().config.DEFAULT_JSON_CLASS
        return json_response_class({"detail": exc.detail}, status_code=exc.status_code)

    # in config.py

    EXCEPTION_HANDLERS = [
        ...,
        error_404_handler
    ]
    """

    def _decorator(f: t.Callable) -> CallableExceptionHandler:
        return CallableExceptionHandler(
            handler=f, exc_or_status_code=exc_or_status_code
        )

    return _decorator
