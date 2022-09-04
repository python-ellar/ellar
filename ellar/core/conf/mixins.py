import typing as t

from starlette.middleware import Middleware
from starlette.responses import JSONResponse

from ellar.core.events import EventHandler
from ellar.core.versioning import BaseAPIVersioning

__all__ = ["ConfigDefaultTypesMixin", "TVersioning", "TMiddleware", "TEventHandler"]


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
    DEBUG: bool
    INJECTOR_AUTO_BIND: bool
    DEFAULT_JSON_CLASS: t.Type[JSONResponse]

    JINJA_TEMPLATES_OPTIONS: t.Dict[str, t.Any]
    VERSIONING_SCHEME: TVersioning

    REDIRECT_SLASHES: bool
    STATIC_FOLDER_PACKAGES: t.Optional[t.List[t.Union[str, t.Tuple[str, str]]]]
    STATIC_DIRECTORIES: t.Optional[t.List[t.Union[str, t.Any]]]

    MIDDLEWARE: t.List[TMiddleware]
    APP_EXCEPTION_HANDLERS: t.Dict[t.Union[int, t.Type[Exception]], t.Callable]

    USER_CUSTOM_EXCEPTION_HANDLERS: t.Dict[t.Union[int, t.Type[Exception]], t.Callable]
    EXCEPTION_HANDLERS: t.Dict[t.Union[int, t.Type[Exception]], t.Callable]
    STATIC_MOUNT_PATH: str

    SERIALIZER_CUSTOM_ENCODER: t.Dict[t.Any, t.Callable[[t.Any], t.Any]]

    MIDDLEWARE_DECORATOR: t.List[TMiddleware]

    ON_REQUEST_STARTUP: t.List[TEventHandler]
    ON_REQUEST_SHUTDOWN: t.List[TEventHandler]

    TEMPLATE_FILTERS: t.Dict[str, t.Callable[..., t.Any]]
    TEMPLATE_GLOBAL_FILTERS: t.Dict[str, t.Callable[..., t.Any]]
