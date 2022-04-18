import typing as t

from starlette import status

from architek.exceptions import APIException, RequestValidationError
from architek.requests import Request
from architek.response import JSONResponse


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    app = request.app
    json_response_type = t.cast(t.Type[JSONResponse], app.config.DEFAULT_JSON_CLASS)

    headers = getattr(exc, "headers", {})
    if isinstance(exc.detail, (list, dict)):
        data = exc.detail
    else:
        data = {"detail": exc.detail}
    return json_response_type(data, status_code=exc.status_code, headers=headers)


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    app = request.app
    json_response_type = t.cast(t.Type[JSONResponse], app.config.DEFAULT_JSON_CLASS)

    return json_response_type(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )
