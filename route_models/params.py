from enum import Enum
from typing import Any, Dict, Optional
from pydantic.fields import FieldInfo, Undefined, ModelField
from . import param_resolvers


class ParamTypes(Enum):
    query = "query"
    header = "header"
    path = "path"
    cookie = "cookie"


class Param(FieldInfo):
    in_: ParamTypes

    def __init__(
            self,
            default: Any,
            *,
            alias: Optional[str] = None,
            title: Optional[str] = None,
            description: Optional[str] = None,
            gt: Optional[float] = None,
            ge: Optional[float] = None,
            lt: Optional[float] = None,
            le: Optional[float] = None,
            min_length: Optional[int] = None,
            max_length: Optional[int] = None,
            regex: Optional[str] = None,
            example: Any = Undefined,
            examples: Optional[Dict[str, Any]] = None,
            deprecated: Optional[bool] = None,
            **extra: Any,
    ):
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

    def get_resolver(self):
        raise NotImplementedError

    def init_resolver(self, model_field: ModelField):
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.default})"


class Path(Param):
    def get_resolver(self):
        return self._resolver

    in_ = ParamTypes.path

    def __init__(
            self,
            default: Any,
            *,
            alias: Optional[str] = None,
            title: Optional[str] = None,
            description: Optional[str] = None,
            gt: Optional[float] = None,
            ge: Optional[float] = None,
            lt: Optional[float] = None,
            le: Optional[float] = None,
            min_length: Optional[int] = None,
            max_length: Optional[int] = None,
            regex: Optional[str] = None,
            example: Any = Undefined,
            examples: Optional[Dict[str, Any]] = None,
            deprecated: Optional[bool] = None,
            **extra: Any,
    ):
        self.in_ = self.in_
        self._resolver = None
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

    def init_resolver(self, model_field: ModelField):
        self._resolver = param_resolvers.PathParameterResolver(model_field)


class Query(Param):
    def get_resolver(self):
        return self._resolver

    in_ = ParamTypes.query

    def __init__(
            self,
            default: Any,
            *,
            alias: Optional[str] = None,
            title: Optional[str] = None,
            description: Optional[str] = None,
            gt: Optional[float] = None,
            ge: Optional[float] = None,
            lt: Optional[float] = None,
            le: Optional[float] = None,
            min_length: Optional[int] = None,
            max_length: Optional[int] = None,
            regex: Optional[str] = None,
            example: Any = Undefined,
            examples: Optional[Dict[str, Any]] = None,
            deprecated: Optional[bool] = None,
            **extra: Any,
    ):
        self._resolver = None
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

    def init_resolver(self, model_field: ModelField):
        self._resolver = param_resolvers.QueryParameterResolver(model_field)


class Header(Param):
    def get_resolver(self):
        return self._resolver

    in_ = ParamTypes.header

    def __init__(
            self,
            default: Any,
            *,
            alias: Optional[str] = None,
            convert_underscores: bool = True,
            title: Optional[str] = None,
            description: Optional[str] = None,
            gt: Optional[float] = None,
            ge: Optional[float] = None,
            lt: Optional[float] = None,
            le: Optional[float] = None,
            min_length: Optional[int] = None,
            max_length: Optional[int] = None,
            regex: Optional[str] = None,
            example: Any = Undefined,
            examples: Optional[Dict[str, Any]] = None,
            deprecated: Optional[bool] = None,
            **extra: Any,
    ):
        self.convert_underscores = convert_underscores
        self._resolver = None

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

    def init_resolver(self, model_field: ModelField):
        self._resolver = param_resolvers.HeaderParameterResolver(model_field)


class Cookie(Param):
    def get_resolver(self):
        return self._resolver

    in_ = ParamTypes.cookie

    def __init__(
            self,
            default: Any,
            *,
            alias: Optional[str] = None,
            title: Optional[str] = None,
            description: Optional[str] = None,
            gt: Optional[float] = None,
            ge: Optional[float] = None,
            lt: Optional[float] = None,
            le: Optional[float] = None,
            min_length: Optional[int] = None,
            max_length: Optional[int] = None,
            regex: Optional[str] = None,
            example: Any = Undefined,
            examples: Optional[Dict[str, Any]] = None,
            deprecated: Optional[bool] = None,
            **extra: Any,
    ):
        self._resolver = None

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

    def init_resolver(self, model_field: ModelField):
        self._resolver = param_resolvers.CookieParameterResolver(model_field)


class Body(FieldInfo):
    def get_resolver(self):
        return self._resolver

    def __init__(
            self,
            default: Any,
            *,
            embed: bool = False,
            media_type: str = "application/json",
            alias: Optional[str] = None,
            title: Optional[str] = None,
            description: Optional[str] = None,
            gt: Optional[float] = None,
            ge: Optional[float] = None,
            lt: Optional[float] = None,
            le: Optional[float] = None,
            min_length: Optional[int] = None,
            max_length: Optional[int] = None,
            regex: Optional[str] = None,
            example: Any = Undefined,
            examples: Optional[Dict[str, Any]] = None,
            **extra: Any,
    ):
        self.embed = embed
        self.media_type = media_type
        self.example = example
        self.examples = examples
        self._resolver = None

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

    def init_resolver(self, model_field: ModelField):
        self._resolver = param_resolvers.BodyParameterResolver(model_field)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.default})"


class Form(Body):
    def get_resolver(self):
        return self._resolver

    def __init__(
            self,
            default: Any,
            *,
            media_type: str = "application/x-www-form-urlencoded",
            alias: Optional[str] = None,
            title: Optional[str] = None,
            description: Optional[str] = None,
            gt: Optional[float] = None,
            ge: Optional[float] = None,
            lt: Optional[float] = None,
            le: Optional[float] = None,
            min_length: Optional[int] = None,
            max_length: Optional[int] = None,
            regex: Optional[str] = None,
            example: Any = Undefined,
            examples: Optional[Dict[str, Any]] = None,
            **extra: Any,
    ):
        self._resolver = None

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

    def init_resolver(self, model_field: ModelField):
        self._resolver = param_resolvers.FormParameterResolver(model_field)


class File(Form):
    def get_resolver(self):
        return self._resolver

    def __init__(
            self,
            default: Any,
            *,
            media_type: str = "multipart/form-data",
            alias: Optional[str] = None,
            title: Optional[str] = None,
            description: Optional[str] = None,
            gt: Optional[float] = None,
            ge: Optional[float] = None,
            lt: Optional[float] = None,
            le: Optional[float] = None,
            min_length: Optional[int] = None,
            max_length: Optional[int] = None,
            regex: Optional[str] = None,
            example: Any = Undefined,
            examples: Optional[Dict[str, Any]] = None,
            **extra: Any,
    ):
        self._resolver = None

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

    def init_resolver(self, model_field: ModelField):
        self._resolver = param_resolvers.FileParameterResolver(model_field)
