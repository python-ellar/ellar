import typing as t

from pydantic.fields import Undefined

from ...params import params


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
    include_in_schema: bool = True,
    **extra: t.Any,
) -> t.Any:
    """
    Defines expected path in Route Function Parameter
    """
    return params.PathFieldInfo(
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
    include_in_schema: bool = True,
    **extra: t.Any,
) -> t.Any:
    """
    Defines expected query in Route Function Parameter
    """
    return params.QueryFieldInfo(
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
        include_in_schema=include_in_schema,
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
    include_in_schema: bool = True,
    **extra: t.Any,
) -> t.Any:
    """
    Defines expected header in Route Function Parameter
    """
    return params.HeaderFieldInfo(
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
        include_in_schema=include_in_schema,
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
    include_in_schema: bool = True,
    **extra: t.Any,
) -> t.Any:
    """
    Defines expected cookie in Route Function Parameter
    """
    return params.CookieFieldInfo(
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
        include_in_schema=include_in_schema,
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
    include_in_schema: bool = True,
    **extra: t.Any,
) -> t.Any:
    """
    Defines expected body object in Route Function Parameter
    """
    return params.BodyFieldInfo(
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
        include_in_schema=include_in_schema,
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
    include_in_schema: bool = True,
    **extra: t.Any,
) -> t.Any:
    """
    Defines expected form parameter in Route Function Parameter
    """
    return params.FormFieldInfo(
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
        include_in_schema=include_in_schema,
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
    include_in_schema: bool = True,
    **extra: t.Any,
) -> t.Any:
    """
    Defines expected file data in Route Function Parameter
    """
    return params.FileFieldInfo(
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
        include_in_schema=include_in_schema,
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
    include_in_schema: bool = True,
    **extra: t.Any,
) -> t.Any:
    """
    Defines expected body object in websocket Route Function Parameter
    """
    return params.WsBodyFieldInfo(
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
        include_in_schema=include_in_schema,
        **extra,
    )
