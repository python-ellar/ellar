"""
Application Configurations
Default Ellar Configurations are exposed here through `ConfigDefaultTypesMixin`
Make changes and define your own configurations specific to your application

export ELLAR_CONFIG_MODULE=db_learning.config:DevelopmentConfig
"""

import typing as t

from ellar.common import IExceptionHandler, JSONResponse
from ellar.core import ConfigDefaultTypesMixin
from ellar.core.versioning import BaseAPIVersioning, DefaultAPIVersioning
from ellar.pydantic import ENCODERS_BY_TYPE as encoders_by_type
from starlette.middleware import Middleware
from starlette.requests import Request


class BaseConfig(ConfigDefaultTypesMixin):
    DEBUG: bool = False

    DEFAULT_JSON_CLASS: t.Type[JSONResponse] = JSONResponse
    SECRET_KEY: str = "ellar_QdZwHTfLkZQWQtAot-V6gbTHONMn3ekrl5jdcb5AOC8"

    # injector auto_bind = True allows you to resolve types that are not registered on the container
    # For more info, read: https://injector.readthedocs.io/en/latest/index.html
    INJECTOR_AUTO_BIND = False

    # jinja Environment options
    # https://jinja.palletsprojects.com/en/3.0.x/api/#high-level-api
    JINJA_TEMPLATES_OPTIONS: t.Dict[str, t.Any] = {}

    # Injects context to jinja templating context values
    TEMPLATES_CONTEXT_PROCESSORS: t.List[
        t.Union[str, t.Callable[[t.Union[Request]], t.Dict[str, t.Any]]]
    ] = [
        "ellar.core.templating.context_processors:request_context",
        "ellar.core.templating.context_processors:user",
        "ellar.core.templating.context_processors:request_state",
    ]

    # Application route versioning scheme
    VERSIONING_SCHEME: BaseAPIVersioning = DefaultAPIVersioning()

    # Enable or Disable Application Router route searching by appending backslash
    REDIRECT_SLASHES: bool = False

    # Define references to static folders in python packages.
    # eg STATIC_FOLDER_PACKAGES = [('boostrap4', 'statics')]
    STATIC_FOLDER_PACKAGES: t.Optional[t.List[t.Union[str, t.Tuple[str, str]]]] = []

    # Define references to static folders defined within the project
    STATIC_DIRECTORIES: t.Optional[t.List[t.Union[str, t.Any]]] = []

    # static route path
    STATIC_MOUNT_PATH: str = "/static"

    CORS_ALLOW_ORIGINS: t.List[str] = ["*"]
    CORS_ALLOW_METHODS: t.List[str] = ["*"]
    CORS_ALLOW_HEADERS: t.List[str] = ["*"]
    ALLOWED_HOSTS: t.List[str] = ["*"]

    # Application middlewares
    MIDDLEWARE: t.Union[str, Middleware] = [
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
    EXCEPTION_HANDLERS: t.Union[str, IExceptionHandler] = [
        "ellar.core.exceptions:error_404_handler"
    ]

    # Object Serializer custom encoders
    SERIALIZER_CUSTOM_ENCODER: t.Dict[t.Any, t.Callable[[t.Any], t.Any]] = (
        encoders_by_type
    )


class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True

    ELLAR_SQL: t.Dict[str, t.Any] = {
        "databases": {
            "default": "sqlite:///app.db",
        },
        "echo": True,
        "migration_options": {
            "directory": "migrations"  # root directory will be determined based on where the module is instantiated.
        },
        "models": ["db_learning.models"],
    }


class TestConfig(BaseConfig):
    DEBUG = False

    ELLAR_SQL: t.Dict[str, t.Any] = {
        **DevelopmentConfig.ELLAR_SQL,
        "databases": {
            "default": "sqlite:///test.db",
        },
        "echo": False,
    }
