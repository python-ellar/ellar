import typing as t

from pydantic.json import ENCODERS_BY_TYPE as encoders_by_type
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp
from starlette.websockets import WebSocketClose

from ellar.constants import DEFAULT_LOGGING as default_logging, LOG_LEVELS as log_levels
from ellar.core.response import PlainTextResponse
from ellar.core.versioning import DefaultAPIVersioning
from ellar.exceptions import APIException, RequestValidationError
from ellar.types import TReceive, TScope, TSend

from ..exception_handlers import (
    api_exception_handler,
    request_validation_exception_handler,
)
from .mixins import ConfigDefaultTypesMixin, TMiddleware, TVersioning

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.main import App


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


class ConfigDefaults(ConfigDefaultTypesMixin):
    DEBUG: bool = False

    DEFAULT_JSON_CLASS: t.Type[JSONResponse] = JSONResponse
    SECRET_KEY: str = "your-secret-key"

    # injector auto_bind = True allows you to resolve types that are not registered on the container
    # For more info, read: https://injector.readthedocs.io/en/latest/index.html
    INJECTOR_AUTO_BIND = False

    # jinja Environment options
    # https://jinja.palletsprojects.com/en/3.0.x/api/#high-level-api
    JINJA_TEMPLATES_OPTIONS: t.Dict[str, t.Any] = {}

    # Application route versioning scheme
    VERSIONING_SCHEME: TVersioning = DefaultAPIVersioning()  # type: ignore

    REDIRECT_SLASHES: bool = False

    STATIC_FOLDER_PACKAGES: t.Optional[t.List[t.Union[str, t.Tuple[str, str]]]] = []

    STATIC_DIRECTORIES: t.Optional[t.List[t.Union[str, t.Any]]] = []

    STATIC_MOUNT_PATH: str = "/static"

    MIDDLEWARE: t.List[TMiddleware] = []

    APP_EXCEPTION_HANDLERS: t.Dict[t.Union[int, t.Type[Exception]], t.Callable] = {
        RequestValidationError: request_validation_exception_handler,
        APIException: api_exception_handler,
    }

    USER_CUSTOM_EXCEPTION_HANDLERS: t.Dict[
        t.Union[int, t.Type[Exception]], t.Callable
    ] = {}

    # Default not found handler
    DEFAULT_NOT_FOUND_HANDLER: ASGIApp = _not_found
    # The lifespan context function is a newer style that replaces
    # on_startup / on_shutdown handlers. Use one or the other, not both.
    DEFAULT_LIFESPAN_HANDLER: t.Optional[
        t.Callable[["App"], t.AsyncContextManager]
    ] = None

    # Object Serializer custom encoders
    SERIALIZER_CUSTOM_ENCODER: t.Dict[
        t.Any, t.Callable[[t.Any], t.Any]
    ] = encoders_by_type

    # logging configuration
    LOGGING_CONFIG: t.Optional[t.Dict[str, t.Any]] = default_logging
    # logging Level
    LOG_LEVEL: t.Optional[log_levels] = log_levels.info
