import typing as t

from starlette import status
from starletteapi.requests import Request
from starletteapi.responses import JSONResponse

from starletteapi.exceptions import RequestValidationError, APIException


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    app = t.cast('StarletteApp', request.app)
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
    app = t.cast('StarletteApp', request.app)
    json_response_type = app.config.DEFAULT_JSON_CLASS
    
    return json_response_type(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )
