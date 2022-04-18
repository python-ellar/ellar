import copy
import re
import sys
import typing as t
from enum import Enum

from pydantic.fields import FieldInfo, ModelField, Undefined

from . import param_resolvers

if sys.version_info >= (3, 6):

    def copier(x: t.Any, memo: t.Dict) -> t.Any:
        return x

    copy._deepcopy_dispatch[type(re.compile(""))] = copier  # type: ignore


class ParamTypes(Enum):
    query = "query"
    header = "header"
    path = "path"
    cookie = "cookie"


class Param(FieldInfo):
    in_: ParamTypes

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
        self._resolver: t.Optional[param_resolvers.RouteParameterResolver] = None
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

    def get_resolver(self) -> param_resolvers.RouteParameterResolver:
        assert self._resolver, "Resolver not initialized"
        return self._resolver

    def init_resolver(self, model_field: ModelField) -> None:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.default})"


class Path(Param):
    in_ = ParamTypes.path

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
        self.in_ = self.in_
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

    def init_resolver(self, model_field: ModelField) -> None:
        self._resolver = param_resolvers.PathParameterResolver(model_field)


class Query(Param):
    in_ = ParamTypes.query

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

    def init_resolver(self, model_field: ModelField) -> None:
        self._resolver = param_resolvers.QueryParameterResolver(model_field)


class Header(Param):
    in_ = ParamTypes.header

    def __init__(
        self,
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
    ) -> None:
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

    def init_resolver(self, model_field: ModelField) -> None:
        self._resolver = param_resolvers.HeaderParameterResolver(model_field)


class Cookie(Param):
    in_ = ParamTypes.cookie

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

    def init_resolver(self, model_field: ModelField) -> None:
        self._resolver = param_resolvers.CookieParameterResolver(model_field)


class Body(FieldInfo):
    def get_resolver(self) -> param_resolvers.RouteParameterResolver:
        assert self._resolver, "Resolver not initialized"
        return self._resolver

    def __init__(
        self,
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
    ) -> None:
        self.embed = embed
        self.media_type = media_type
        self.example = example
        self.examples = examples
        self._resolver: t.Optional[param_resolvers.RouteParameterResolver] = None

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

    def init_resolver(self, model_field: ModelField) -> None:
        self._resolver = param_resolvers.BodyParameterResolver(model_field)
        body_resolvers = model_field.field_info.extra.get("body_resolvers")
        if body_resolvers:
            model_field.field_info.extra.pop("body_resolvers")
            self._resolver = param_resolvers.BulkBodyParameterResolver(
                model_field, resolvers=body_resolvers
            )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.default})"


class WsBody(Body):
    def init_resolver(self, model_field: ModelField) -> None:
        self._resolver = param_resolvers.WsBodyParameterResolver(model_field)


class Form(Body):
    def __init__(
        self,
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
    ) -> None:

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

    def init_resolver(self, model_field: ModelField) -> None:
        self._resolver = param_resolvers.FormParameterResolver(model_field)
        body_resolvers = model_field.field_info.extra.get("body_resolvers")
        if body_resolvers:
            model_field.field_info.extra.pop("body_resolvers")
            self._resolver = param_resolvers.BulkFormParameterResolver(
                model_field, form_resolvers=body_resolvers
            )


class File(Form):
    def __init__(
        self,
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
    ) -> None:

        super().__init__(
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

    def init_resolver(self, model_field: ModelField) -> None:
        self._resolver = param_resolvers.FileParameterResolver(model_field)
