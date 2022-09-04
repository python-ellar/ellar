import typing as t

from pydantic import Field, root_validator, validator
from pydantic.json import ENCODERS_BY_TYPE
from starlette.responses import JSONResponse

from ellar.constants import LOG_LEVELS
from ellar.core.exception_handlers import (
    api_exception_handler,
    request_validation_exception_handler,
)
from ellar.core.versioning import DefaultAPIVersioning
from ellar.exceptions import APIException, RequestValidationError
from ellar.serializer import Serializer, SerializerFilter

from .mixins import ConfigDefaultTypesMixin, TEventHandler, TMiddleware, TVersioning


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
    INJECTOR_AUTO_BIND: bool = False
    DEFAULT_JSON_CLASS: t.Type[JSONResponse] = JSONResponse
    VERSIONING_SCHEME: TVersioning = Field(DefaultAPIVersioning())
    JINJA_TEMPLATES_OPTIONS: t.Dict[str, t.Any] = {}
    REDIRECT_SLASHES: bool = False
    STATIC_FOLDER_PACKAGES: t.Optional[t.List[t.Union[str, t.Tuple[str, str]]]] = []
    STATIC_DIRECTORIES: t.Optional[t.List[t.Union[str, t.Any]]] = []

    MIDDLEWARE: t.List[TMiddleware] = []
    APP_EXCEPTION_HANDLERS: t.Dict[t.Union[int, t.Type[Exception]], t.Callable] = {
        RequestValidationError: request_validation_exception_handler,
        APIException: api_exception_handler,
    }

    USER_CUSTOM_EXCEPTION_HANDLERS: t.Dict[
        t.Union[int, t.Type[Exception]], t.Callable
    ] = {}
    EXCEPTION_HANDLERS: t.Dict[t.Union[int, t.Type[Exception]], t.Callable] = {}
    STATIC_MOUNT_PATH: str = "/static"

    SERIALIZER_CUSTOM_ENCODER: t.Dict[t.Any, t.Callable[[t.Any], t.Any]] = {}

    MIDDLEWARE_DECORATOR: t.List[TMiddleware] = []

    ON_REQUEST_STARTUP: t.List[TEventHandler] = []
    ON_REQUEST_SHUTDOWN: t.List[TEventHandler] = []

    TEMPLATE_FILTERS: t.Dict[str, t.Callable[..., t.Any]] = {}
    TEMPLATE_GLOBAL_FILTERS: t.Dict[str, t.Callable[..., t.Any]] = {}

    LOGGING: t.Optional[t.Dict[str, t.Any]] = None
    LOG_LEVEL: t.Optional[LOG_LEVELS] = LOG_LEVELS.info
    ASGI_APPLICATION: t.Optional[str] = None
    APPLICATION_MODULE: t.Optional[str] = None

    @root_validator(pre=False)
    def pre_root_validate(cls, values: t.Any) -> t.Any:
        app_exception_handlers = dict(values["APP_EXCEPTION_HANDLERS"])
        user_custom_exception_handlers = values.get(
            "USER_CUSTOM_EXCEPTION_HANDLERS", {}
        )

        app_exception_handlers.update(**user_custom_exception_handlers)

        values["EXCEPTION_HANDLERS"] = app_exception_handlers
        middleware_decorator_handlers = list(values.get("MIDDLEWARE_DECORATOR", []))
        user_settings_middleware = list(values.get("MIDDLEWARE", []))
        middleware_decorator_handlers.extend(user_settings_middleware)
        values["MIDDLEWARE"] = middleware_decorator_handlers

        return values

    @validator("MIDDLEWARE", pre=True)
    def pre_middleware_validate(cls, value: t.Any) -> t.Any:
        if isinstance(value, tuple):
            return list(value)
        return value

    @validator("SERIALIZER_CUSTOM_ENCODER")
    def serializer_custom_encoder(cls, value: t.Any) -> t.Any:
        encoder = dict(ENCODERS_BY_TYPE)
        encoder.update(value)
        return encoder

    @validator("STATIC_MOUNT_PATH", pre=True)
    def pre_static_mount_path(cls, value: t.Any) -> t.Any:
        assert value.startswith("/"), "Routed paths must start with '/'"
        return value
