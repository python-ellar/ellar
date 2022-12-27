import inspect
import typing as t

from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from ellar.constants import LOG_LEVELS as log_levels
from ellar.core.events import EventHandler
from ellar.core.exceptions.interfaces import IExceptionHandler
from ellar.core.middleware import Middleware
from ellar.core.versioning import BaseAPIVersioning

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core import App

__all__ = [
    "ConfigDefaultTypesMixin",
    "TVersioning",
    "TMiddleware",
    "TEventHandler",
    "TExceptionHandler",
]


class TExceptionHandler:
    @classmethod
    def __get_validators__(
        cls: t.Type["TExceptionHandler"],
    ) -> t.Iterable[t.Callable[..., t.Any]]:
        yield cls.validate

    @classmethod
    def validate(cls: t.Type["TExceptionHandler"], v: t.Any) -> t.Any:
        if isinstance(v, IExceptionHandler):
            return v

        if inspect.isclass(v):
            raise ValueError(f"Expected TExceptionHandler, received: {v}")

        raise ValueError(f"Expected TExceptionHandler, received: {type(v)}")


class TVersioning(BaseAPIVersioning):
    @classmethod
    def __get_validators__(
        cls: t.Type["TVersioning"],
    ) -> t.Iterable[t.Callable[..., t.Any]]:
        yield cls.validate

    @classmethod
    def validate(cls: t.Type["BaseAPIVersioning"], v: t.Any) -> t.Any:
        if not isinstance(v, BaseAPIVersioning):
            raise ValueError(f"Expected BaseAPIVersioning, received: {type(v)}")
        return v


class TMiddleware(Middleware):
    @classmethod
    def __get_validators__(
        cls: t.Type["TMiddleware"],
    ) -> t.Iterable[t.Callable[..., t.Any]]:
        yield cls.validate

    @classmethod
    def validate(cls: t.Type["Middleware"], v: t.Any) -> t.Any:
        if not isinstance(v, Middleware):
            raise ValueError(f"Expected Middleware, received: {type(v)}")
        return v


class TEventHandler(EventHandler):
    @classmethod
    def __get_validators__(
        cls: t.Type["TEventHandler"],
    ) -> t.Iterable[t.Callable[..., t.Any]]:
        yield cls.validate

    @classmethod
    def validate(cls: t.Type["EventHandler"], v: t.Any) -> t.Any:
        if not isinstance(v, EventHandler):
            raise ValueError(f"Expected EventHandler, received: {type(v)}")
        return v


class ConfigDefaultTypesMixin:
    SECRET_KEY: str
    DEBUG: bool
    # injector auto_bind = True allows you to resolve types that are not registered on the container
    # For more info, read: https://injector.readthedocs.io/en/latest/index.html
    INJECTOR_AUTO_BIND: bool

    # Default JSON response class
    DEFAULT_JSON_CLASS: t.Type[JSONResponse]

    # jinja Environment options
    # https://jinja.palletsprojects.com/en/3.0.x/api/#high-level-api
    JINJA_TEMPLATES_OPTIONS: t.Dict[str, t.Any]

    # Application route versioning scheme
    VERSIONING_SCHEME: TVersioning

    # Enable or Disable Application Router route searching by appending backslash
    REDIRECT_SLASHES: bool

    # Define references to static folders in python packages.
    # eg STATIC_FOLDER_PACKAGES = [('boostrap4', 'statics')]
    STATIC_FOLDER_PACKAGES: t.Optional[t.List[t.Union[str, t.Tuple[str, str]]]]

    # Define references to static folders defined within the project
    STATIC_DIRECTORIES: t.Optional[t.List[t.Union[str, t.Any]]]

    # Application user defined middlewares
    MIDDLEWARE: t.List[TMiddleware]

    # A dictionary mapping either integer status codes,
    # or exception class types onto callables which handle the exceptions.
    # Exception handler callables should be of the form
    # `handler(request, exc) -> response` and may be either standard functions, or async functions.
    EXCEPTION_HANDLERS: t.List[IExceptionHandler]

    # static route
    STATIC_MOUNT_PATH: str

    # defines other custom json encoders
    SERIALIZER_CUSTOM_ENCODER: t.Dict[t.Any, t.Callable[[t.Any], t.Any]]

    # will be set automatically when @on_startup is found in a Module class
    ON_REQUEST_STARTUP: t.List[TEventHandler]

    # will be set automatically when @on_shutdown is found in a Module class
    ON_REQUEST_SHUTDOWN: t.List[TEventHandler]

    # will be set automatically when @template_filter is found in a Module class
    TEMPLATE_FILTERS: t.Dict[str, t.Callable[..., t.Any]]

    # will be set automatically when @template_global is found in a Module class
    TEMPLATE_GLOBAL_FILTERS: t.Dict[str, t.Callable[..., t.Any]]

    # Default not found handler
    DEFAULT_NOT_FOUND_HANDLER: ASGIApp

    # The lifespan context function is a newer style that replaces
    # on_startup / on_shutdown handlers. Use one or the other, not both.
    DEFAULT_LIFESPAN_HANDLER: t.Optional[t.Callable[["App"], t.AsyncContextManager]]

    # logging configuration
    LOGGING_CONFIG: t.Optional[t.Dict[str, t.Any]]

    # logging Level
    LOG_LEVEL: t.Optional[log_levels]

    # CORS Middleware setup (ellar.core.middleware.CORSMiddleware)
    CORS_ALLOW_ORIGINS: t.List[str]
    CORS_ALLOW_METHODS: t.List[str]
    CORS_ALLOW_HEADERS: t.List[str]
    CORS_ALLOW_CREDENTIALS: bool

    CORS_ALLOW_ORIGIN_REGEX: t.Optional[str]
    CORS_EXPOSE_HEADERS: t.Sequence[str]
    CORS_MAX_AGE: int

    # TrustHostMiddleware setup
    ALLOWED_HOSTS: t.List[str]
    REDIRECT_HOST: bool
