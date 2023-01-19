import typing as t

from pydantic.fields import Undefined
from starlette.responses import Response

from ellar.core.connection import HTTPConnection, Request, WebSocket
from ellar.core.context import IExecutionContext
from ellar.core.params import params
from ellar.core.params.resolvers.non_parameter import (
    ConnectionParam,
    ExecutionContextParameter,
    HostRequestParam,
    ProviderParameterInjector,
    RequestParameter,
    ResponseRequestParam,
    SessionRequestParam,
    WebSocketParameter,
)
from ellar.types import T


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
    """
    Defines expected path in Route Function Parameter
    """
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
    """
    Defines expected query in Route Function Parameter
    """
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
    """
    Defines expected header in Route Function Parameter
    """
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
    """
    Defines expected cookie in Route Function Parameter
    """
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
    """
    Defines expected body object in Route Function Parameter
    """
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
    """
    Defines expected form parameter in Route Function Parameter
    """
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
    """
    Defines expected file data in Route Function Parameter
    """
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
    """
    Defines expected body object in websocket Route Function Parameter
    """
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


def Http() -> HTTPConnection:
    """
    Route Function Parameter for retrieving Current Request Instance
    :return: Request
    """
    return t.cast(Request, ConnectionParam())


def Req() -> Request:
    """
    Route Function Parameter for retrieving Current Request Instance
    :return: Request
    """
    return t.cast(Request, RequestParameter())


def Ws() -> WebSocket:
    """
    Route Function Parameter for retrieving Current WebSocket Instance
    :return: WebSocket
    """
    return t.cast(WebSocket, WebSocketParameter())


def Context() -> IExecutionContext:
    """
    Route Function Parameter for retrieving Current IExecutionContext Instance
    :return: IExecutionContext
    """
    return t.cast(IExecutionContext, ExecutionContextParameter())


def Provide(service: t.Optional[t.Type[T]] = None) -> T:
    """
    Route Function Parameter for resolving registered Provider
    :return: T
    """
    return t.cast(T, ProviderParameterInjector(service))


def Session() -> t.Dict:
    """
    Route Function Parameter for resolving registered `HTTPConnection.sessions`
    Ensure SessionMiddleware is registered to application middlewares
    :return: Dict
    """
    return t.cast(t.Dict, SessionRequestParam())


def Host() -> str:
    """
    Route Function Parameter for resolving registered `HTTPConnection.client.host`
    :return: str
    """
    return t.cast(str, HostRequestParam())


def Res() -> Response:
    """
    Route Function Parameter for resolving registered Response
    :return: Response
    """
    return t.cast(Response, ResponseRequestParam())
