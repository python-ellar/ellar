from ellar.common import IExecutionContext
from starlette.exceptions import HTTPException
from starlette.responses import Response

from .callable_exceptions import CallableExceptionHandler, as_exception_handler
from .service import ExceptionMiddlewareService

__all__ = [
    "ExceptionMiddlewareService",
    "error_404_handler",
    "as_exception_handler",
    "CallableExceptionHandler",
]


@as_exception_handler(404)
async def error_404_handler(ctx: IExecutionContext, exc: HTTPException) -> Response:
    json_response_class = ctx.get_app().config.DEFAULT_JSON_CLASS
    return json_response_class({"detail": exc.detail}, status_code=exc.status_code)
