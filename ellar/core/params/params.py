import copy
import re
import sys
import typing as t
from enum import Enum

from pydantic.fields import FieldInfo, ModelField, Undefined

from ellar.constants import MULTI_RESOLVER_KEY

from .resolvers import (
    BodyParameterResolver,
    BulkBodyParameterResolver,
    BulkFormParameterResolver,
    BulkParameterResolver,
    CookieParameterResolver,
    FileParameterResolver,
    FormParameterResolver,
    HeaderParameterResolver,
    PathParameterResolver,
    QueryParameterResolver,
    RouteParameterResolver,
    WsBodyParameterResolver,
)

if sys.version_info >= (3, 6):

    def copier(x: t.Any, memo: t.Dict) -> t.Any:
        return x

    copy._deepcopy_dispatch[type(re.compile(""))] = copier  # type: ignore


class ParamTypes(Enum):
    query = "query"
    header = "header"
    path = "path"
    cookie = "cookie"
    body = "body"


class Param(FieldInfo):
    in_: ParamTypes = ParamTypes.query
    resolver: t.Type[RouteParameterResolver] = QueryParameterResolver
    bulk_resolver: t.Type[BulkParameterResolver] = BulkParameterResolver

    def __init__(
        self,
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
    ) -> None:
        self.deprecated = deprecated
        self.example = example
        self.examples = examples
        super().__init__(
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
            **extra,
        )

    def create_resolver(self, model_field: ModelField) -> RouteParameterResolver:
        multiple_resolvers = model_field.field_info.extra.get(MULTI_RESOLVER_KEY)
        if multiple_resolvers:
            model_field.field_info.extra.pop(MULTI_RESOLVER_KEY)
            return self.bulk_resolver(
                model_field=model_field, resolvers=multiple_resolvers
            )
        return self.resolver(model_field)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.default})"


class Path(Param):
    in_ = ParamTypes.path
    resolver: t.Type[RouteParameterResolver] = PathParameterResolver

    def __init__(
        self,
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
    ) -> None:
        super().__init__(
            ...,
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
            deprecated=deprecated,
            example=example,
            examples=examples,
            **extra,
        )


class Query(Param):
    in_ = ParamTypes.query
    resolver: t.Type[RouteParameterResolver] = QueryParameterResolver


class Header(Param):
    in_ = ParamTypes.header
    resolver: t.Type[RouteParameterResolver] = HeaderParameterResolver

    def __init__(
        self,
        default: t.Any,
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
    ):
        self.convert_underscores = convert_underscores
        super().__init__(
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
            deprecated=deprecated,
            example=example,
            examples=examples,
            **extra,
        )


class Cookie(Param):
    in_ = ParamTypes.cookie
    resolver: t.Type[RouteParameterResolver] = CookieParameterResolver


class Body(Param):
    in_ = ParamTypes.body
    MEDIA_TYPE: str = "application/json"
    resolver: t.Type[RouteParameterResolver] = BodyParameterResolver
    bulk_resolver: t.Type[BulkParameterResolver] = BulkBodyParameterResolver

    def __init__(
        self,
        default: t.Any = ...,
        *,
        embed: bool = False,
        media_type: t.Optional[str] = None,
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
    ) -> None:
        self.embed = embed
        self.media_type = media_type or self.MEDIA_TYPE

        super().__init__(
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
            examples=examples,
            example=example,
            **extra,
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.default})"


class WsBody(Body):
    resolver: t.Type[RouteParameterResolver] = WsBodyParameterResolver


class Form(Body):
    resolver: t.Type[RouteParameterResolver] = FormParameterResolver
    MEDIA_TYPE: str = "application/x-www-form-urlencoded"
    bulk_resolver: t.Type[BulkParameterResolver] = BulkFormParameterResolver

    def __init__(
        self,
        default: t.Any,
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
    ):
        super().__init__(
            default,
            embed=True,
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


class File(Form):
    resolver: t.Type[RouteParameterResolver] = FileParameterResolver
    MEDIA_TYPE: str = "multipart/form-data"
