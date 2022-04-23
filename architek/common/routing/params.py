import typing as t

from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import Undefined

from architek.core.connection import Request, WebSocket
from architek.core.context import ExecutionContext
from architek.core.params import params
from architek.core.params.resolvers import (
    NonFieldRouteParameterResolver,
    ParameterInjectable,
)
from architek.types import T


def Path(
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
    example: t.Any = Undefined,
    examples: t.Optional[t.Dict[str, t.Any]] = None,
    deprecated: t.Optional[bool] = None,
    **extra: t.Any,
) -> t.Any:
    return params.Path(
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
        **extra,
    )


def Query(
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
    example: t.Any = Undefined,
    examples: t.Optional[t.Dict[str, t.Any]] = None,
    deprecated: t.Optional[bool] = None,
    **extra: t.Any,
) -> t.Any:
    return params.Query(
        default,
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
        **extra,
    )


def Header(
    default: t.Any = ...,
    *,
    alias: t.Optional[str] = None,
    convert_underscores: bool = True,
    title: t.Optional[str] = None,
    description: t.Optional[str] = None,
    gt: t.Optional[float] = None,
    ge: t.Optional[float] = None,
    lt: t.Optional[float] = None,
    le: t.Optional[float] = None,
    min_length: t.Optional[int] = None,
    max_length: t.Optional[int] = None,
    regex: t.Optional[str] = None,
    example: t.Any = Undefined,
    examples: t.Optional[t.Dict[str, t.Any]] = None,
    deprecated: t.Optional[bool] = None,
    **extra: t.Any,
) -> t.Any:
    return params.Header(
        default,
        alias=alias,
        convert_underscores=convert_underscores,
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
        **extra,
    )


def Cookie(
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
    example: t.Any = Undefined,
    examples: t.Optional[t.Dict[str, t.Any]] = None,
    deprecated: t.Optional[bool] = None,
    **extra: t.Any,
) -> t.Any:
    return params.Cookie(
        default,
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
        **extra,
    )


def Body(
    default: t.Any = ...,
    *,
    embed: bool = False,
    media_type: str = "application/json",
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
    example: t.Any = Undefined,
    examples: t.Optional[t.Dict[str, t.Any]] = None,
    **extra: t.Any,
) -> t.Any:
    return params.Body(
        default,
        embed=embed,
        media_type=media_type,
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
        **extra,
    )


def Form(
    default: t.Any = ...,
    *,
    media_type: str = "application/x-www-form-urlencoded",
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
    example: t.Any = Undefined,
    examples: t.Optional[t.Dict[str, t.Any]] = None,
    **extra: t.Any,
) -> t.Any:
    return params.Form(
        default,
        media_type=media_type,
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
        **extra,
    )


def File(
    default: t.Any = ...,
    *,
    media_type: str = "multipart/form-data",
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
    example: t.Any = Undefined,
    examples: t.Optional[t.Dict[str, t.Any]] = None,
    **extra: t.Any,
) -> t.Any:
    return params.File(
        default,
        media_type=media_type,
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
        **extra,
    )


def WsBody(
    default: t.Any = ...,
    *,
    embed: bool = False,
    media_type: str = "application/json",
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
    example: t.Any = Undefined,
    examples: t.Optional[t.Dict[str, t.Any]] = None,
    **extra: t.Any,
) -> t.Any:
    return params.WsBody(
        default,
        embed=embed,
        media_type=media_type,
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
        **extra,
    )


class _RequestParameter(NonFieldRouteParameterResolver):
    async def resolve(
        self, ctx: ExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.List]:
        try:
            request = ctx.switch_to_request()
            return {self.parameter_name: request}, []
        except Exception as ex:
            return {}, [ErrorWrapper(ex, loc=self.parameter_name or "request")]


class _WebSocketParameter(NonFieldRouteParameterResolver):
    async def resolve(
        self, ctx: ExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.List]:
        try:
            websocket = ctx.switch_to_websocket()
            return {self.parameter_name: websocket}, []
        except Exception as ex:
            return {}, [ErrorWrapper(ex, loc=self.parameter_name or "websocket")]


class _ExecutionContextParameter(NonFieldRouteParameterResolver):
    async def resolve(
        self, ctx: ExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.List]:
        return {self.parameter_name: ctx}, []


def req() -> Request:
    return t.cast(Request, _RequestParameter())


def ws() -> WebSocket:
    return t.cast(WebSocket, _WebSocketParameter())


def cxt() -> ExecutionContext:
    return t.cast(ExecutionContext, _ExecutionContextParameter())


def provide(service: t.Optional[t.Type[T]] = None) -> T:
    return t.cast(T, ParameterInjectable(service))
