import typing as t

from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import Undefined
from starlette.responses import Response

from ellar.core.connection import HTTPConnection, Request, WebSocket
from ellar.core.context import IExecutionContext
from ellar.core.params import params
from ellar.core.params.resolvers import (
    BaseRequestRouteParameterResolver,
    NonFieldRouteParameterResolver,
    ParameterInjectable,
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


class _RequestParameter(NonFieldRouteParameterResolver):
    async def resolve(
        self, ctx: IExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.List]:
        try:
            request = ctx.switch_to_http_connection().get_request()
            return {self.parameter_name: request}, []
        except Exception as ex:
            return {}, [ErrorWrapper(ex, loc=self.parameter_name or "request")]


class _WebSocketParameter(NonFieldRouteParameterResolver):
    async def resolve(
        self, ctx: IExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.List]:
        try:
            websocket = ctx.switch_to_websocket().get_client()
            return {self.parameter_name: websocket}, []
        except Exception as ex:
            return {}, [ErrorWrapper(ex, loc=self.parameter_name or "websocket")]


class _ExecutionContextParameter(NonFieldRouteParameterResolver):
    async def resolve(
        self, ctx: IExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.List]:
        return {self.parameter_name: ctx}, []


class _HostRequestParam(BaseRequestRouteParameterResolver):
    lookup_connection_field = None

    async def get_value(self, ctx: IExecutionContext) -> t.Any:
        connection = ctx.switch_to_http_connection().get_client()
        if connection.client:
            return connection.client.host


class _SessionRequestParam(BaseRequestRouteParameterResolver):
    lookup_connection_field = "session"


class _ConnectionParam(NonFieldRouteParameterResolver):
    async def resolve(
        self, ctx: IExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.List]:
        try:
            connection = ctx.switch_to_http_connection().get_client()
            return {self.parameter_name: connection}, []
        except Exception as ex:
            return {}, [ErrorWrapper(ex, loc=self.parameter_name or "connection")]


class _ResponseRequestParam(NonFieldRouteParameterResolver):
    async def resolve(
        self, ctx: IExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.List]:
        try:
            response = ctx.switch_to_http_connection().get_response()
            return {self.parameter_name: response}, []
        except Exception as ex:
            return {}, [ErrorWrapper(ex, loc=self.parameter_name or "response")]


def Http() -> HTTPConnection:
    """
    Route Function Parameter for retrieving Current Request Instance
    :return: Request
    """
    return t.cast(Request, _ConnectionParam())


def Req() -> Request:
    """
    Route Function Parameter for retrieving Current Request Instance
    :return: Request
    """
    return t.cast(Request, _RequestParameter())


def Ws() -> WebSocket:
    """
    Route Function Parameter for retrieving Current WebSocket Instance
    :return: WebSocket
    """
    return t.cast(WebSocket, _WebSocketParameter())


def Context() -> IExecutionContext:
    """
    Route Function Parameter for retrieving Current IExecutionContext Instance
    :return: IExecutionContext
    """
    return t.cast(IExecutionContext, _ExecutionContextParameter())


def Provide(service: t.Optional[t.Type[T]] = None) -> T:
    """
    Route Function Parameter for resolving registered Provider
    :return: T
    """
    return t.cast(T, ParameterInjectable(service))


def Session() -> t.Dict:
    """
    Route Function Parameter for resolving registered `HTTPConnection.sessions`
    Ensure SessionMiddleware is registered to application middlewares
    :return: Dict
    """
    return t.cast(t.Dict, _SessionRequestParam())


def Host() -> str:
    """
    Route Function Parameter for resolving registered `HTTPConnection.client.host`
    :return: str
    """
    return t.cast(str, _HostRequestParam())


def Res() -> Response:
    """
    Route Function Parameter for resolving registered Response
    :return: Response
    """
    return t.cast(Response, _ResponseRequestParam())
