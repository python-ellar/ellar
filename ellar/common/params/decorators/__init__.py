import typing as t

from typing_extensions import Annotated

from . import models as param_functions
from .inject import InjectShortcut, add_default_resolver, get_default_resolver

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
        alias: t.Optional[str] = None,
        title: t.Optional[str] = None,
        description: t.Optional[str] = None,
        gt: t.Optional[float] = None,
        ge: t.Optional[float] = None,
        lt: t.Optional[float] = None,
        le: t.Optional[float] = None,
        min_length: t.Optional[int] = None,
        max_length: t.Optional[int] = None,
        regex: t.Optional[str] = None,
        example: t.Any = None,
        examples: t.Optional[t.Dict[str, t.Any]] = None,
        deprecated: t.Optional[bool] = None,
        include_in_schema: bool = True,
        **extra: t.Any,
    ) -> t.Dict[str, t.Any]:
        """Arguments for Body, Query, Header, Cookie, etc."""
        return dict(
            default=default,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            regex=regex,
            example=example,
            examples=examples,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
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
    Inject = Annotated[T, t.Any]

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
