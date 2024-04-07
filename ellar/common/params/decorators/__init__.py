import typing as t

from ellar.pydantic.types import Undefined
from ellar.utils import get_name
from typing_extensions import Annotated

from . import models as param_functions
from .inject import InjectShortcut, add_default_resolver, get_default_resolver

_Unset: t.Any = Undefined


__all__ = [
    "add_default_resolver",
    "get_default_resolver",
    "Body",
    "Cookie",
    "File",
    "Form",
    "Header",
    "Path",
    "Query",
    "WsBody",
    "Inject",
]


class _ParamShortcut:
    def __init__(self, base_func: t.Callable) -> None:
        self._base_func = base_func
        self.name = get_name(base_func)

    def __call__(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        return self._base_func(*args, **kwargs)

    def __getitem__(self, args: t.Any) -> t.Any:
        if isinstance(args, tuple):
            return Annotated[args[0], self._base_func(**args[1])]
        return Annotated[args, self._base_func()]

    @classmethod
    def P(
        cls,
        default: t.Any = ...,
        *,
        default_factory: t.Union[t.Callable[[], t.Any], None] = _Unset,
        alias: t.Optional[str] = None,
        alias_priority: t.Union[int, None] = _Unset,
        validation_alias: t.Union[str, None] = None,
        serialization_alias: t.Union[str, None] = None,
        title: t.Optional[str] = None,
        description: t.Optional[str] = None,
        gt: t.Optional[float] = None,
        ge: t.Optional[float] = None,
        lt: t.Optional[float] = None,
        le: t.Optional[float] = None,
        min_length: t.Optional[int] = None,
        max_length: t.Optional[int] = None,
        pattern: t.Optional[str] = None,
        discriminator: t.Union[str, None] = None,
        strict: t.Union[bool, None] = _Unset,
        multiple_of: t.Union[float, None] = _Unset,
        allow_inf_nan: t.Union[bool, None] = _Unset,
        max_digits: t.Union[int, None] = _Unset,
        decimal_places: t.Union[int, None] = _Unset,
        examples: t.Optional[t.List[t.Any]] = None,
        deprecated: t.Optional[bool] = None,
        include_in_schema: bool = True,
        json_schema_extra: t.Union[t.Dict[str, t.Any], None] = None,
        **extra: t.Any,
    ) -> t.Dict[str, t.Any]:
        """Arguments for Body, Query, Header, Cookie, etc."""
        return dict(
            default=default,
            default_factory=default_factory,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            discriminator=discriminator,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            pattern=pattern,
            alias_priority=alias_priority,
            validation_alias=validation_alias,
            serialization_alias=serialization_alias,
            strict=strict,
            json_schema_extra=json_schema_extra,
            examples=examples,
            include_in_schema=include_in_schema,
            deprecated=deprecated,
            **extra,
        )


if t.TYPE_CHECKING:  # pragma: nocover
    # mypy cheats
    T = t.TypeVar("T")
    Body = Annotated[T, param_functions.Body()]
    Cookie = Annotated[T, param_functions.Cookie()]
    File = Annotated[T, param_functions.File()]
    Form = Annotated[T, param_functions.Form()]
    Header = Annotated[T, param_functions.Header()]
    Path = Annotated[T, param_functions.Path()]
    Query = Annotated[T, param_functions.Query()]
    WsBody = Annotated[T, param_functions.WsBody()]
    Inject = Annotated[T, InjectShortcut()]

else:
    Body = _ParamShortcut(param_functions.Body)
    Cookie = _ParamShortcut(param_functions.Cookie)
    File = _ParamShortcut(param_functions.File)
    Form = _ParamShortcut(param_functions.Form)
    Header = _ParamShortcut(param_functions.Header)
    Path = _ParamShortcut(param_functions.Path)
    Query = _ParamShortcut(param_functions.Query)
    WsBody = _ParamShortcut(param_functions.WsBody)
    Inject = InjectShortcut()
