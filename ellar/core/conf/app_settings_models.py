import sys
import typing as t

from ellar.common.constants import (
    DEFAULT_LOGGING as default_logging,
)
from ellar.common.constants import (
    LOG_LEVELS as log_levels,
)
from ellar.common.interfaces import IAPIVersioning, IEllarMiddleware, IExceptionHandler
from ellar.common.responses import JSONResponse, PlainTextResponse
from ellar.common.serializer import Serializer, SerializerFilter
from ellar.common.types import ASGIApp, TReceive, TScope, TSend
from ellar.core.versioning import DefaultAPIVersioning
from pydantic import validator
from pydantic.json import ENCODERS_BY_TYPE as encoders_by_type
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.websockets import WebSocketClose

from .mixins import ConfigDefaultTypesMixin

if sys.version_info >= (3, 8):  # pragma: no cover
    from typing import Literal
else:  # pragma: no cover
    from typing_extensions import Literal
if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.app.main import App


async def _not_found(
    scope: TScope, receive: TReceive, send: TSend
) -> None:  # pragma: no cover
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

    # injector auto_bind = True allows you to resolve types that are not registered on the container
    # For more info, read: https://injector.readthedocs.io/en/latest/index.html
    INJECTOR_AUTO_BIND = False

    # jinja Environment options
    # https://jinja.palletsprojects.com/en/3.0.x/api/#high-level-api
    JINJA_TEMPLATES_OPTIONS: t.Dict[str, t.Any] = {}

    # Application route versioning scheme
    VERSIONING_SCHEME: IAPIVersioning = DefaultAPIVersioning()

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

    MIDDLEWARE: t.List[IEllarMiddleware] = []

    EXCEPTION_HANDLERS: t.List[IExceptionHandler] = []

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

    TEMPLATE_FILTERS: t.Dict[str, t.Callable[..., t.Any]] = {}
    TEMPLATE_GLOBAL_FILTERS: t.Dict[str, t.Callable[..., t.Any]] = {}

    LOGGING: t.Optional[t.Dict[str, t.Any]] = None
    CACHES: t.Dict[str, t.Any] = {}

    SESSION_COOKIE_NAME: str = "session"
    SESSION_COOKIE_DOMAIN: t.Optional[str] = None
    SESSION_COOKIE_PATH: str = "/"
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SECURE: bool = False
    SESSION_COOKIE_SAME_SITE: Literal["lax", "strict", "none"] = "lax"
    SESSION_COOKIE_MAX_AGE: t.Optional[int] = 14 * 24 * 60 * 60  # 14 days, in seconds

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

    @validator("CACHES", pre=True)
    def pre_cache_validate(cls, value: t.Dict) -> t.Any:
        if value and not value.get("default"):
            raise ValueError("CACHES configuration must have a 'default' key")
        return value
