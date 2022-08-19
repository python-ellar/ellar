import typing as t

from pydantic import Field, root_validator, validator
from pydantic.json import ENCODERS_BY_TYPE
from starlette.middleware import Middleware
from starlette.responses import JSONResponse

from ellar.core.events import EventHandler
from ellar.core.versioning import BaseAPIVersioning, DefaultAPIVersioning
from ellar.serializer import Serializer, SerializerFilter


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


class ConfigValidationSchema(Serializer):
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

    JINJA_TEMPLATES_OPTIONS: t.Dict[str, t.Any] = {}
    VERSIONING_SCHEME: TVersioning = Field(DefaultAPIVersioning())

    REDIRECT_SLASHES: bool = False
    STATIC_FOLDER_PACKAGES: t.Optional[t.List[t.Union[str, t.Tuple[str]]]] = []
    STATIC_DIRECTORIES: t.Optional[t.List[t.Union[str, t.Any]]] = []

    MIDDLEWARE: t.List[TMiddleware] = []
    APP_EXCEPTION_HANDLERS: t.Dict[t.Union[int, t.Type[Exception]], t.Callable] = {}

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
    INJECTOR_AUTO_BIND: bool = False

    @root_validator(pre=True)
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
