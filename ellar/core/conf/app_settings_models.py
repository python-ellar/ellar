import typing as t

from ellar.common import EllarInterceptor, GuardCanActivate
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
from ellar.core.conf.mixins import ConfigDefaultTypesMixin
from ellar.di import ProviderConfig
from ellar.di.injector.tree_manager import ModuleTreeManager
from ellar.pydantic import ENCODERS_BY_TYPE as encoders_by_type
from ellar.pydantic import AllowTypeOfSource, field_validator
from jinja2 import BaseLoader
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware import Middleware
from starlette.requests import HTTPConnection, Request
from starlette.websockets import WebSocketClose
from typing_extensions import Annotated

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.app.main import App

TEMPLATE_TYPE = t.Dict[
    str, t.Union[t.Callable[..., t.Any], t.Dict[str, t.Callable[..., t.Any]]]
]


_TemplateProcessorValidator = AllowTypeOfSource(
    validator=lambda source, value: callable(value),
    error_message=lambda source, value: f"Expected a callable, got {type(value)}",
)
TemplateProcessorType = Annotated[
    t.Callable[[t.Union[Request, HTTPConnection]], t.Dict[str, t.Any]],
    _TemplateProcessorValidator,
]

_VersioningValidator = AllowTypeOfSource(
    error_message=lambda source,
    value: f"Expected BaseAPIVersioning, received: {type(value)}"
)
VersioningType = Annotated[IAPIVersioning, _VersioningValidator]

_MiddlewareValidator = AllowTypeOfSource(
    validator=lambda source, value: isinstance(value, (source, Middleware)),
    error_message=lambda source,
    value: f"Expected EllarMiddleware or Starlette Middleware object, received: {type(value)}",
)
MiddlewareType = Annotated[IEllarMiddleware, _MiddlewareValidator]

_ExceptionHandlerValidator = AllowTypeOfSource(
    error_message=lambda source,
    value: f"Expected IExceptionHandler object, received: {type(value)}"
)
ExceptionHandlerType = Annotated[IExceptionHandler, _ExceptionHandlerValidator]

_GuardValidator = AllowTypeOfSource(
    validator=lambda source, value: (
        issubclass(value, GuardCanActivate)
        if isinstance(value, type)
        else isinstance(value, GuardCanActivate)
    ),
    error_message=lambda source,
    value: f"Expected GuardCanActivate object or type, received: {type(value)}",
)
GuardCanActivateType = Annotated[GuardCanActivate, _GuardValidator]

_InterceptorValidator = AllowTypeOfSource(
    validator=lambda source, value: (
        issubclass(value, EllarInterceptor)
        if isinstance(value, type)
        else isinstance(value, EllarInterceptor)
    ),
    error_message=lambda source,
    value: f"Expected GuardCanActivate object or type, received: {type(value)}",
)
InterceptorType = Annotated[EllarInterceptor, _InterceptorValidator]

_JinjaLoaderValidator = AllowTypeOfSource(
    error_message=lambda source,
    value: f"Expected {BaseLoader} object, received: {type(value)}",
)
JinjaLoaderType = Annotated[BaseLoader, _JinjaLoaderValidator]


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


class ConfigSchema(Serializer, ConfigDefaultTypesMixin):
    _filter = SerializerFilter(
        exclude={
            "EXCEPTION_HANDLERS_DECORATOR",
            "MIDDLEWARE_DECORATOR",
            "APP_EXCEPTION_HANDLERS",
            "USER_CUSTOM_EXCEPTION_HANDLERS",
        }
    )

    model_config = {
        "validate_assignment": True,
        "validate_default": True,
        "from_attributes": True,
        "extra": "allow",
    }

    OVERRIDE_CORE_SERVICE: t.List[Annotated[ProviderConfig, AllowTypeOfSource()]] = []

    GLOBAL_GUARDS: t.List[GuardCanActivateType] = []

    GLOBAL_INTERCEPTORS: t.List[InterceptorType] = []

    DEBUG: bool = False

    DEFAULT_JSON_CLASS: t.Type[JSONResponse] = JSONResponse

    MODULE_TREE_MANAGER_CLASS: t.Type[ModuleTreeManager] = ModuleTreeManager

    SECRET_KEY: str = "your-secret-key"

    # injector auto_bind = True allows you to resolve types that are not registered on the container
    # For more info, read: https://injector.readthedocs.io/en/latest/index.html
    INJECTOR_AUTO_BIND: bool = False

    # jinja Environment options
    # https://jinja.palletsprojects.com/en/3.0.x/api/#high-level-api
    JINJA_TEMPLATES_OPTIONS: t.Dict[str, t.Any] = {}
    JINJA_LOADERS: t.List[JinjaLoaderType] = []

    TEMPLATES_CONTEXT_PROCESSORS: t.List[TemplateProcessorType] = [  # type:ignore[assignment]
        "ellar.core.templating.context_processors:request_context",
        "ellar.core.templating.context_processors:user",
        "ellar.core.templating.context_processors:request_state",
    ]

    # Application route versioning scheme
    VERSIONING_SCHEME: t.Optional[VersioningType] = None

    REDIRECT_SLASHES: bool = False

    STATIC_FOLDER_PACKAGES: t.Optional[t.List[t.Union[str, t.Tuple[str, str]]]] = []

    STATIC_DIRECTORIES: t.Optional[t.List[t.Union[str, t.Any]]] = []

    STATIC_MOUNT_PATH: t.Optional[str] = "/static"

    CORS_ALLOW_ORIGINS: t.List[str] = []
    CORS_ALLOW_METHODS: t.List[str] = ["GET"]
    CORS_ALLOW_HEADERS: t.List[str] = []

    CORS_ALLOW_CREDENTIALS: bool = False
    CORS_ALLOW_ORIGIN_REGEX: t.Optional[str] = None
    CORS_EXPOSE_HEADERS: t.List[str] = []
    CORS_MAX_AGE: int = 600

    ALLOWED_HOSTS: t.List[str] = ["*"]
    REDIRECT_HOST: bool = True

    MIDDLEWARE: t.List[MiddlewareType] = [
        "ellar.core.middleware.trusted_host:trusted_host_middleware",
        "ellar.core.middleware.cors:cors_middleware",
        "ellar.core.middleware.errors:server_error_middleware",
        "ellar.core.middleware.versioning:versioning_middleware",
        "ellar.auth.middleware.session:session_middleware",
        "ellar.auth.middleware.auth:identity_middleware",
        "ellar.core.middleware.exceptions:exception_middleware",
    ]
    # A dictionary mapping either integer status codes,
    # or exception class types onto callables which handle the exceptions.
    # Exception handler callables should be of the form
    # `handler(context:IExecutionContext, exc: Exception) -> response`
    # and may be either standard functions, or async functions.
    EXCEPTION_HANDLERS: t.List[ExceptionHandlerType] = [
        "ellar.core.exceptions:error_404_handler"
    ]

    # Default not found handler
    DEFAULT_NOT_FOUND_HANDLER: ASGIApp = _not_found
    # The lifespan context function is a newer style that replaces
    # on_startup / on_shutdown handlers. Use one or the other, not both.
    DEFAULT_LIFESPAN_HANDLER: t.Optional[t.Callable[["App"], t.AsyncContextManager]] = (
        None
    )

    # Object Serializer custom encoders
    SERIALIZER_CUSTOM_ENCODER: t.Dict[t.Any, t.Callable[[t.Any], t.Any]] = (
        encoders_by_type
    )

    # logging configuration
    LOGGING_CONFIG: t.Optional[t.Dict[str, t.Any]] = default_logging
    # logging Level
    LOG_LEVEL: t.Optional[log_levels] = log_levels.info

    TEMPLATE_FILTERS: TEMPLATE_TYPE = {}
    TEMPLATE_GLOBAL_FILTERS: TEMPLATE_TYPE = {}

    LOGGING: t.Optional[t.Dict[str, t.Any]] = None
    CACHES: t.Dict[str, t.Any] = {}

    SESSION_COOKIE_NAME: str = "session"
    SESSION_COOKIE_DOMAIN: t.Optional[str] = None
    SESSION_COOKIE_PATH: str = "/"
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SECURE: bool = False
    SESSION_COOKIE_SAME_SITE: t.Literal["lax", "strict", "none"] = "lax"
    SESSION_COOKIE_MAX_AGE: t.Optional[int] = 14 * 24 * 60 * 60  # 14 days, in seconds

    @field_validator("MIDDLEWARE", mode="before")
    def pre_middleware_validate(cls, value: t.Any) -> t.Any:
        if isinstance(value, tuple):
            return list(value)
        return value

    @field_validator("SERIALIZER_CUSTOM_ENCODER")
    def serializer_custom_encoder(cls, value: t.Any) -> t.Any:
        encoder = dict(encoders_by_type)
        encoder.update(value)
        return encoder

    @field_validator("STATIC_MOUNT_PATH", mode="before")
    def pre_static_mount_path(cls, value: t.Any) -> t.Any:
        if value:
            assert value.startswith("/"), "Routed paths must start with '/'"
        return value

    @field_validator("CACHES", mode="before")
    def pre_cache_validate(cls, value: t.Dict) -> t.Any:
        if value and not value.get("default"):
            raise ValueError("CACHES configuration must have a 'default' key")
        return value
