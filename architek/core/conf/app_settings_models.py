import typing as t

from pydantic import Field, root_validator, validator
from starlette.middleware import Middleware
from starlette.responses import JSONResponse

from architek.core.schema import PydanticSchema
from architek.core.versioning import BaseAPIVersioning, DefaultAPIVersioning


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


class StarletteAPIConfig(PydanticSchema):
    class Config:
        orm_mode = True
        validate_assignment = True

    DEBUG: bool = False
    DEFAULT_JSON_CLASS: t.Type[JSONResponse] = JSONResponse

    TEMPLATES_AUTO_RELOAD: t.Optional[bool] = None
    VERSIONING_SCHEME: TVersioning = Field(DefaultAPIVersioning())

    REDIRECT_SLASHES: bool = False
    STATIC_FOLDER_PACKAGES: t.Optional[t.List[t.Union[str, t.Tuple[str]]]] = []

    MIDDLEWARE: t.List[TMiddleware] = []
    APP_EXCEPTION_HANDLERS: t.Dict[t.Union[int, t.Type[Exception]], t.Callable] = {}

    USER_CUSTOM_EXCEPTION_HANDLERS: t.Dict[
        t.Union[int, t.Type[Exception]], t.Callable
    ] = {}
    EXCEPTION_HANDLERS: t.Dict[t.Union[int, t.Type[Exception]], t.Callable] = {}
    STATIC_MOUNT_PATH: str = "/static"

    @root_validator(pre=True)
    def pre_root_validate(cls, values: t.Any) -> t.Any:
        app_exception_handlers = dict(values["APP_EXCEPTION_HANDLERS"])
        user_custom_exception_handlers = values["USER_CUSTOM_EXCEPTION_HANDLERS"]
        app_exception_handlers.update(**user_custom_exception_handlers)
        values["EXCEPTION_HANDLERS"] = app_exception_handlers
        return values

    @validator("MIDDLEWARE", pre=True)
    def pre_middleware_validate(cls, value: t.Any) -> t.Any:
        if isinstance(value, tuple):
            return list(value)
        return value

    @validator("STATIC_MOUNT_PATH", pre=True)
    def pre_static_mount_path(cls, value: t.Any) -> t.Any:
        assert value.startswith("/"), "Routed paths must start with '/'"
        return value
