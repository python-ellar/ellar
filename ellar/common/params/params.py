import typing as t
from enum import Enum

from ellar.common.constants import MULTI_RESOLVER_FORM_GROUPED_KEY, MULTI_RESOLVER_KEY
from ellar.pydantic import FieldInfo, ModelField
from ellar.pydantic import types as pydantic_types

from .resolvers import (
    BaseRouteParameterResolver,
    BodyParameterResolver,
    BulkBodyParameterResolver,
    BulkFormParameterResolver,
    BulkParameterResolver,
    CookieParameterResolver,
    FileParameterResolver,
    FormParameterResolver,
    HeaderParameterResolver,
    IRouteParameterResolver,
    PathParameterResolver,
    QueryParameterResolver,
    WsBodyParameterResolver,
)

_Unset: t.Any = pydantic_types.Undefined


class ParamTypes(Enum):
    query = "query"
    header = "header"
    path = "path"
    cookie = "cookie"
    body = "body"


class ParamFieldInfo(FieldInfo):
    in_: ParamTypes = ParamTypes.query
    resolver: t.Type[BaseRouteParameterResolver] = QueryParameterResolver
    bulk_resolver: t.Type[BulkParameterResolver] = BulkParameterResolver

    def __init__(
        self,
        default: t.Any = pydantic_types.Undefined,
        *,
        default_factory: t.Union[t.Callable[[], t.Any], None] = _Unset,
        annotation: t.Optional[t.Any] = None,
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
    ):
        # identifies a field wrapping many resolvers/field-infos
        self._ellar_body = extra.pop("ellar_body", False)

        self.deprecated = deprecated
        self.include_in_schema = include_in_schema

        if serialization_alias in (_Unset, None) and isinstance(alias, str):
            serialization_alias = alias

        if validation_alias in (_Unset, None):
            validation_alias = alias

        kwargs = dict(
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
            allow_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            pattern=pattern,
            annotation=annotation,
            alias_priority=alias_priority,
            validation_alias=validation_alias,
            serialization_alias=serialization_alias,
            strict=strict,
            json_schema_extra=json_schema_extra or extra,
            **extra,
        )
        if examples is not None:  # pragma: no cover
            kwargs["examples"] = examples
        init_kwargs = {k: v for k, v in kwargs.items() if v is not _Unset}

        super().__init__(**init_kwargs)

    def create_resolver(
        self, model_field: ModelField
    ) -> t.Union[BaseRouteParameterResolver, IRouteParameterResolver]:
        """
        Create a resolver for a given model field.

        This method is responsible for creating the appropriate resolver for a given
        model field.
        It checks if the model field has been split into many sub-models that are referred to as MultipleResolvers.
        And then creates an appropriate resolver for each of them.

        Args:
            model_field (ModelField): The model field to create a resolver for.

        Returns:
            BaseRouteParameterResolver: The created resolver.
        """
        multiple_resolvers = model_field.field_info.json_schema_extra.pop(  # type:ignore[union-attr]
            MULTI_RESOLVER_KEY, None
        )
        if multiple_resolvers:
            return self.bulk_resolver(
                model_field=model_field,
                resolvers=multiple_resolvers,  # type:ignore[arg-type]
            )
        return self.resolver(model_field)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.default})"


class PathFieldInfo(ParamFieldInfo):
    in_ = ParamTypes.path
    resolver: t.Type[BaseRouteParameterResolver] = PathParameterResolver

    def __init__(
        self,
        default: t.Any = ...,
        *,
        default_factory: t.Union[t.Callable[[], t.Any], None] = _Unset,
        annotation: t.Optional[t.Any] = None,
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
    ):
        super().__init__(
            default=default,
            default_factory=default_factory,
            annotation=annotation,
            alias=alias,
            alias_priority=alias_priority,
            validation_alias=validation_alias,
            serialization_alias=serialization_alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            discriminator=discriminator,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            deprecated=deprecated,
            examples=examples,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )


class QueryFieldInfo(ParamFieldInfo):
    in_ = ParamTypes.query
    resolver: t.Type[BaseRouteParameterResolver] = QueryParameterResolver


class HeaderFieldInfo(ParamFieldInfo):
    in_ = ParamTypes.header
    resolver: t.Type[BaseRouteParameterResolver] = HeaderParameterResolver

    def __init__(
        self,
        default: t.Any = ...,
        *,
        convert_underscores: bool = True,
        default_factory: t.Union[t.Callable[[], t.Any], None] = _Unset,
        annotation: t.Optional[t.Any] = None,
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
    ):
        self.convert_underscores = convert_underscores
        super().__init__(
            default=default,
            default_factory=default_factory,
            annotation=annotation,
            alias=alias,
            alias_priority=alias_priority,
            validation_alias=validation_alias,
            serialization_alias=serialization_alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            discriminator=discriminator,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            deprecated=deprecated,
            examples=examples,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )


class CookieFieldInfo(ParamFieldInfo):
    in_ = ParamTypes.cookie
    resolver: t.Type[BaseRouteParameterResolver] = CookieParameterResolver


class BodyFieldInfo(ParamFieldInfo):
    in_ = ParamTypes.body
    MEDIA_TYPE: str = "application/json"
    resolver: t.Type[BaseRouteParameterResolver] = BodyParameterResolver
    bulk_resolver: t.Type[BulkParameterResolver] = BulkBodyParameterResolver

    def __init__(
        self,
        default: t.Any = ...,
        *,
        embed: bool = False,
        media_type: t.Optional[str] = None,
        default_factory: t.Union[t.Callable[[], t.Any], None] = _Unset,
        annotation: t.Optional[t.Any] = None,
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
    ) -> None:
        self.embed = embed
        self.media_type = media_type or self.MEDIA_TYPE

        super().__init__(
            default=default,
            default_factory=default_factory,
            annotation=annotation,
            alias=alias,
            alias_priority=alias_priority,
            validation_alias=validation_alias,
            serialization_alias=serialization_alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            discriminator=discriminator,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            deprecated=deprecated,
            examples=examples,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.default})"


class WsBodyFieldInfo(BodyFieldInfo):
    resolver: t.Type[BaseRouteParameterResolver] = WsBodyParameterResolver


class FormFieldInfo(ParamFieldInfo):
    in_ = ParamTypes.body
    resolver: t.Type[BaseRouteParameterResolver] = FormParameterResolver
    MEDIA_TYPE: str = "application/form-data"
    bulk_resolver: t.Type[BulkParameterResolver] = BulkFormParameterResolver

    def __init__(
        self,
        default: t.Any = ...,
        *,
        media_type: t.Optional[str] = None,
        default_factory: t.Union[t.Callable[[], t.Any], None] = _Unset,
        annotation: t.Optional[t.Any] = None,
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
    ):
        super().__init__(
            default=default,
            default_factory=default_factory,
            annotation=annotation,
            alias=alias,
            alias_priority=alias_priority,
            validation_alias=validation_alias,
            serialization_alias=serialization_alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            discriminator=discriminator,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            deprecated=deprecated,
            examples=examples,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )
        self.embed = True
        self.media_type = media_type or self.MEDIA_TYPE

    def create_resolver(
        self, model_field: ModelField
    ) -> t.Union[BaseRouteParameterResolver, IRouteParameterResolver]:
        multiple_resolvers = model_field.field_info.json_schema_extra.pop(  # type:ignore[union-attr]
            MULTI_RESOLVER_KEY, []
        )
        is_grouped = model_field.field_info.json_schema_extra.pop(  # type:ignore[union-attr]
            MULTI_RESOLVER_FORM_GROUPED_KEY, False
        )

        if multiple_resolvers:
            return self.bulk_resolver(
                model_field=model_field,
                resolvers=multiple_resolvers,  # type:ignore[arg-type]
                is_grouped=is_grouped,
            )
        return self.resolver(model_field)


class FileFieldInfo(FormFieldInfo):
    resolver: t.Type[BaseRouteParameterResolver] = FileParameterResolver
    MEDIA_TYPE: str = "multipart/form-data"
