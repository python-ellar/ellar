from typing import Any, cast, Type, TYPE_CHECKING

from starlette import status
from starlette.requests import Request
from starletteapi.responses import JSONResponse

from starletteapi.exceptions import RequestValidationError, APIException
if TYPE_CHECKING:
    from .main import StarletteApp


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    app = cast('StarletteApp', request.app)
    json_response_type = app.config.DEFAULT_JSON_CLASS

    headers = getattr(exc, "headers", {})
    if isinstance(exc.detail, (list, dict)):
        data = exc.detail
    else:
        data = {"detail": exc.detail}
    return json_response_type(
        data, status_code=exc.status_code, headers=headers
    )


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    app = cast('StarletteApp', request.app)
    json_response_type = app.config.DEFAULT_JSON_CLASS
    
    return json_response_type(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )
