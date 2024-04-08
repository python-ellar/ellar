"""
Application Configurations
Default Ellar Configurations are exposed here through `ConfigDefaultTypesMixin`
Make changes and define your own configurations specific to your application

export ELLAR_CONFIG_MODULE=ellar_storage_tut.config:DevelopmentConfig
"""
import os
import typing as t
from pathlib import Path

from ellar.common import IExceptionHandler, JSONResponse
from ellar.core import ConfigDefaultTypesMixin
from ellar.core.versioning import BaseAPIVersioning, DefaultAPIVersioning
from ellar.pydantic import ENCODERS_BY_TYPE as encoders_by_type
from starlette.middleware import Middleware

from ellar_storage import Provider, get_driver

BASE_DIRS = Path(__file__).parent


class BaseConfig(ConfigDefaultTypesMixin):
    DEBUG: bool = False

    DEFAULT_JSON_CLASS: t.Type[JSONResponse] = JSONResponse
    SECRET_KEY: str = "ellar_ugl4IS-ZjJxJ0dH_hfJb8ZCwK31595uS4aaBqXYO4Sg"

    # injector auto_bind = True allows you to resolve types that are not registered on the container
    # For more info, read: https://injector.readthedocs.io/en/latest/index.html
    INJECTOR_AUTO_BIND = False

    # jinja Environment options
    # https://jinja.palletsprojects.com/en/3.0.x/api/#high-level-api
    JINJA_TEMPLATES_OPTIONS: t.Dict[str, t.Any] = {}

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
    MIDDLEWARE: t.Sequence[Middleware] = []

    # A dictionary mapping either integer status codes,
    # or exception class types onto callables which handle the exceptions.
    # Exception handler callables should be of the form
    # `handler(context:IExecutionContext, exc: Exception) -> response`
    # and may be either standard functions, or async functions.
    EXCEPTION_HANDLERS: t.List[IExceptionHandler] = []

    # Object Serializer custom encoders
    SERIALIZER_CUSTOM_ENCODER: t.Dict[
        t.Any, t.Callable[[t.Any], t.Any]
    ] = encoders_by_type

    STORAGE_CONFIG = dict(
        storages=dict(
            files={
                "driver": get_driver(Provider.LOCAL),
                "options": {"key": os.path.join(BASE_DIRS, "media")},
            },
            images={
                "driver": get_driver(Provider.LOCAL),
                "options": {"key": os.path.join(BASE_DIRS, "media")},
            },
            documents={
                "driver": get_driver(Provider.LOCAL),
                "options": {"key": os.path.join(BASE_DIRS, "media")},
            }
        ),
        default="files"
    )


class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True
