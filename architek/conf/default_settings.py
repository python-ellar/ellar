import typing as t

from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from starlette.websockets import WebSocketClose

from architek.exception_handlers import (
    api_exception_handler,
    request_validation_exception_handler,
)
from architek.exceptions import APIException, RequestValidationError
from architek.response import PlainTextResponse
from architek.types import TReceive, TScope, TSend
from architek.versioning import BaseAPIVersioning, DefaultAPIVersioning

if t.TYPE_CHECKING:
    from architek.main import ArchitekApp

DEBUG: bool = False

DEFAULT_JSON_CLASS: t.Type[JSONResponse] = JSONResponse
SECRET_KEY: str = "your-secret-key"

TEMPLATES_AUTO_RELOAD: t.Optional[bool] = None

VERSIONING_SCHEME: BaseAPIVersioning = DefaultAPIVersioning()
REDIRECT_SLASHES: bool = False

STATIC_FOLDER_PACKAGES: t.Optional[t.List[t.Union[str, t.Tuple[str]]]] = []
STATIC_MOUNT_PATH: str = "/static"

MIDDLEWARE: t.Sequence[Middleware] = []

APP_EXCEPTION_HANDLERS: t.Dict[t.Union[int, t.Type[Exception]], t.Callable] = {
    RequestValidationError: request_validation_exception_handler,
    APIException: api_exception_handler,
}

# A dictionary mapping either integer status codes,
# or exception class types onto callables which handle the exceptions.
# Exception handler callables should be of the form
# `handler(request, exc) -> response` and may be be either standard functions, or async functions.
USER_CUSTOM_EXCEPTION_HANDLERS: t.Dict[t.Union[int, t.Type[Exception]], t.Callable] = {}


async def _not_found(scope: TScope, receive: TReceive, send: TSend) -> None:
    if scope["type"] == "websocket":
        websocket_close = WebSocketClose()
        await websocket_close(scope, receive, send)
        return

    # If we're running inside a starlette application then raise an
    # exception, so that the configurable exception handler can deal with
    # returning the response. For plain ASGI apps, just return the response.
    if "app" in scope:
        raise StarletteHTTPException(status_code=404)
    else:
        response = PlainTextResponse("Not Found", status_code=404)
    await response(scope, receive, send)


DEFAULT_NOT_FOUND_HANDLER: t.Callable[
    [TScope, TReceive, TSend], t.Coroutine[t.Any, t.Any, None]
] = _not_found
# The lifespan context function is a newer style that replaces
# on_startup / on_shutdown handlers. Use one or the other, not both.
DEFAULT_LIFESPAN_HANDLER: t.Optional[
    t.Callable[["ArchitekApp"], t.AsyncContextManager]
] = None
