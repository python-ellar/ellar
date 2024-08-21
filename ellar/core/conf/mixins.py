import typing as t

from ellar.common import EllarInterceptor, GuardCanActivate
from ellar.common.constants import LOG_LEVELS as log_levels
from ellar.common.interfaces import IAPIVersioning, IEllarMiddleware, IExceptionHandler
from ellar.di import ProviderConfig
from ellar.di.injector.tree_manager import ModuleTreeManager
from jinja2 import BaseLoader
from starlette.requests import HTTPConnection, Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.app import App

__all__ = [
    "ConfigDefaultTypesMixin",
]


class ConfigDefaultTypesMixin:
    OVERRIDE_CORE_SERVICE: t.List[ProviderConfig]

    SECRET_KEY: str

    DEBUG: bool
    # injector auto_bind = True allows you to resolve types that are not registered on the container
    # For more info, read: https://injector.readthedocs.io/en/latest/index.html
    INJECTOR_AUTO_BIND: bool

    # Default JSON response class
    DEFAULT_JSON_CLASS: t.Type[JSONResponse]

    MODULE_TREE_MANAGER_CLASS: t.Type[ModuleTreeManager]

    # jinja Environment options
    # https://jinja.palletsprojects.com/en/3.0.x/api/#high-level-api
    JINJA_TEMPLATES_OPTIONS: t.Dict[str, t.Any]

    JINJA_LOADERS: t.List[BaseLoader]

    TEMPLATES_CONTEXT_PROCESSORS: t.List[
        t.Callable[[t.Union[Request, HTTPConnection]], t.Dict[str, t.Any]]
    ]

    # Application route versioning scheme
    VERSIONING_SCHEME: t.Optional[IAPIVersioning]

    # Enable or Disable Application Router route searching by appending backslash
    REDIRECT_SLASHES: bool

    # Define references to static folders in python packages.
    # eg STATIC_FOLDER_PACKAGES = [('boostrap4', 'statics')]
    STATIC_FOLDER_PACKAGES: t.Optional[t.List[t.Union[str, t.Tuple[str, str]]]]

    # Define references to static folders defined within the project
    STATIC_DIRECTORIES: t.Optional[t.List[t.Union[str, t.Any]]]

    # Application user defined middlewares
    MIDDLEWARE: t.List[IEllarMiddleware]

    # A dictionary mapping either integer status codes,
    # or exception class types onto callables which handle the exceptions.
    # Exception handler callables should be of the form
    # `handler(request, exc) -> response` and may be either standard functions, or async functions.
    EXCEPTION_HANDLERS: t.List[IExceptionHandler]

    # static route
    STATIC_MOUNT_PATH: t.Optional[str]

    # defines other custom json encoders
    SERIALIZER_CUSTOM_ENCODER: t.Dict[t.Any, t.Callable[[t.Any], t.Any]]

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

    # CORS Middleware setup (ellar.middleware.CORSMiddleware)
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
    # Cache Module setup
    CACHES: t.Dict[str, t.Any]
    # Application Global Guards
    GLOBAL_GUARDS: t.List[t.Union[GuardCanActivate, t.Type[GuardCanActivate]]]
    # Application Global Interceptors
    GLOBAL_INTERCEPTORS: t.List[t.Union[EllarInterceptor, t.Type[EllarInterceptor]]]
