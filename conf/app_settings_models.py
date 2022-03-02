import typing as t

from pydantic import validator

from starletteapi.schema import PydanticSchema
from starlette.middleware import Middleware
from starlette.responses import JSONResponse

from starletteapi.versioning import BaseAPIVersioning, DefaultAPIVersioning


class StarletteAPIConfig(PydanticSchema):
    class Config:
        orm_mode = True
        validate_assignment = True
        arbitrary_types_allowed = True

    DEBUG: bool = False
    DEFAULT_JSON_CLASS: t.Type[JSONResponse] = JSONResponse

    TEMPLATES_AUTO_RELOAD: t.Optional[bool] = None
    VERSIONING_SCHEME: BaseAPIVersioning = DefaultAPIVersioning()

    REDIRECT_SLASHES: bool = False
    STATIC_FOLDER_PACKAGES: t.Optional[t.List[t.Union[str, t.Tuple[str]]]] = []

    MIDDLEWARE: t.List[Middleware] = []
    APP_EXCEPTION_HANDLERS: t.Dict[t.Union[int, t.Type[Exception]], t.Callable] = {}

    USER_CUSTOM_EXCEPTION_HANDLERS: t.Dict[t.Union[int, t.Type[Exception]], t.Callable] = {}
    EXCEPTION_HANDLERS: t.Dict[t.Union[int, t.Type[Exception]], t.Callable] = {}
    STATIC_MOUNT_PATH: str = '/static'

    @validator("EXCEPTION_HANDLERS")
    def exception_handlers_validator(cls, values: t.Any) -> t.Any:
        app_exception_handlers = values['APP_EXCEPTION_HANDLERS']
        user_custom_exception_handlers = values['USER_CUSTOM_EXCEPTION_HANDLERS']
        app_exception_handlers.update(**user_custom_exception_handlers)
        return app_exception_handlers

    @validator("MIDDLEWARE", pre=True)
    def pre_middleware_validate(cls, value: t.Any) -> t.Any:
        if isinstance(value, tuple):
            return list(value)
        return value

    @validator("STATIC_MOUNT_PATH", pre=True)
    def pre_static_mount_path(cls, value: t.Any) -> t.Any:
        assert value.startswith("/"), "Routed paths must start with '/'"
        return value
