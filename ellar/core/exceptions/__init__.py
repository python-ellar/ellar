from ellar.common import IExecutionContext
from ellar.common.exceptions import CallableExceptionHandler
from starlette.exceptions import HTTPException
from starlette.responses import Response

from .service import ExceptionMiddlewareService

__all__ = [
    "ExceptionMiddlewareService",
    "error_404_handler",
]


async def _404_error_handler(ctx: IExecutionContext, exc: HTTPException) -> Response:
    json_response_class = ctx.get_app().config.DEFAULT_JSON_CLASS
    return json_response_class({"detail": exc.detail}, status_code=exc.status_code)


error_404_handler = CallableExceptionHandler(
    exc_or_status_code=404, handler=_404_error_handler
)
