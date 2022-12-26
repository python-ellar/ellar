import typing as t

from pydantic import Field, validator
from pydantic.json import ENCODERS_BY_TYPE as encoders_by_type
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.websockets import WebSocketClose

from ellar.constants import DEFAULT_LOGGING as default_logging, LOG_LEVELS as log_levels
from ellar.core.response import JSONResponse, PlainTextResponse
from ellar.core.versioning import DefaultAPIVersioning
from ellar.serializer import Serializer, SerializerFilter
from ellar.types import ASGIApp, TReceive, TScope, TSend

from .mixins import (
    ConfigDefaultTypesMixin,
    TEventHandler,
    TExceptionHandler,
    TMiddleware,
    TVersioning,
)

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


class ConfigValidationSchema(Serializer, ConfigDefaultTypesMixin):
    _filter = SerializerFilter(
        exclude={
            "EXCEPTION_HANDLERS_DECORATOR",
            "MIDDLEWARE_DECORATOR",
            "APP_EXCEPTION_HANDLERS",
            "USER_CUSTOM_EXCEPTION_HANDLERS",
        }
    )

    class Config:
        orm_mode = True
        validate_assignment = True

    DEBUG: bool = False

    DEFAULT_JSON_CLASS: t.Type[JSONResponse] = JSONResponse

    SECRET_KEY: str = "your-secret-key"

    VERSIONING_SCHEME: TVersioning = Field(DefaultAPIVersioning())
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

    CORS_ALLOW_ORIGINS: t.List[str] = []
    CORS_ALLOW_METHODS: t.List[str] = ["GET"]
    CORS_ALLOW_HEADERS: t.List[str] = []

    CORS_ALLOW_CREDENTIALS: bool = False
    CORS_ALLOW_ORIGIN_REGEX: t.Optional[str] = None
    CORS_EXPOSE_HEADERS: t.Sequence[str] = ()
    CORS_MAX_AGE: int = 600

    ALLOWED_HOSTS: t.List[str] = ["*"]
    REDIRECT_HOST: bool = True

    MIDDLEWARE: t.List[TMiddleware] = []

    EXCEPTION_HANDLERS: t.List[TExceptionHandler] = []  # type:ignore

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

    ON_REQUEST_STARTUP: t.List[TEventHandler] = []
    ON_REQUEST_SHUTDOWN: t.List[TEventHandler] = []

    TEMPLATE_FILTERS: t.Dict[str, t.Callable[..., t.Any]] = {}
    TEMPLATE_GLOBAL_FILTERS: t.Dict[str, t.Callable[..., t.Any]] = {}

    LOGGING: t.Optional[t.Dict[str, t.Any]] = None

    @validator("MIDDLEWARE", pre=True)
    def pre_middleware_validate(cls, value: t.Any) -> t.Any:
        if isinstance(value, tuple):
            return list(value)
        return value

    @validator("SERIALIZER_CUSTOM_ENCODER")
    def serializer_custom_encoder(cls, value: t.Any) -> t.Any:
        encoder = dict(encoders_by_type)
        encoder.update(value)
        return encoder

    @validator("STATIC_MOUNT_PATH", pre=True)
    def pre_static_mount_path(cls, value: t.Any) -> t.Any:
        assert value.startswith("/"), "Routed paths must start with '/'"
        return value
