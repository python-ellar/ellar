import typing as t

from ellar.common.interfaces import IExecutionContext
from ellar.common.logger import request_logger
from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import ModelField

from .base import BaseRouteParameterResolver
from .parameter import BodyParameterResolver, FormParameterResolver


class BulkParameterResolver(BaseRouteParameterResolver):
    def __init__(
        self,
        *args: t.Any,
        resolvers: t.List[BaseRouteParameterResolver],
        **kwargs: t.Any,
    ):
        super().__init__(*args, **kwargs)
        self._resolvers = resolvers or []

    @property
    def resolvers(self) -> t.List[BaseRouteParameterResolver]:
        return self._resolvers

    def get_model_fields(self) -> t.List[ModelField]:
        return [resolver.model_field for resolver in self._resolvers]

    async def resolve_handle(
        self, ctx: IExecutionContext, *args: t.Any, **kwargs: t.Any
    ) -> t.Tuple:
        request_logger.debug(
            f"Resolving Bulk Path Parameters - '{self.__class__.__name__}'"
        )
        values: t.Dict[str, t.Any] = {}
        errors: t.List[ErrorWrapper] = []

        for parameter_resolver in self._resolvers:
            value_, errors_ = await parameter_resolver.resolve(ctx=ctx)
            if value_:
                values.update(value_)
            if errors_:
                errors += self.validate_error_sequence(errors_)
        if errors:
            return values, errors

        v_, errors_ = self.model_field.validate(
            values,
            {},
            loc=(self.model_field.field_info.in_.value, self.model_field.alias),
        )
        if errors_:
            errors += self.validate_error_sequence(errors_)
            return values, errors
        return {self.model_field.name: v_}, []


class BulkFormParameterResolver(FormParameterResolver, BulkParameterResolver):
    def __init__(self, *args: t.Any, is_grouped: bool = False, **kwargs: t.Any):
        super().__init__(*args, **kwargs)
        self.is_grouped = is_grouped
        self._use_resolver: t.Callable[
            [IExecutionContext, t.Any], t.Awaitable[t.Tuple]
        ] = t.cast(
            t.Callable[[IExecutionContext, t.Any], t.Awaitable[t.Tuple]],
            self.resolve_grouped_fields
            if is_grouped
            else self.resolve_ungrouped_fields,
        )

    async def resolve_grouped_fields(
        self, ctx: IExecutionContext, body: t.Any
    ) -> t.Tuple:
        request_logger.debug(
            f"Resolving Form Grouped Field - '{self.__class__.__name__}'"
        )
        value, resolver_errors = await self._get_resolver_data(ctx, body)
        if resolver_errors:
            return value, resolver_errors

        processed_value, processed_errors = self.model_field.validate(
            value,
            {},
            loc=(self.model_field.field_info.in_.value, self.model_field.alias),
        )
        if processed_errors:
            processed_errors = self.validate_error_sequence(processed_errors)
            return processed_value, processed_errors
        return {self.model_field.name: processed_value}, []

    async def resolve_ungrouped_fields(
        self, ctx: IExecutionContext, body: t.Any
    ) -> t.Tuple:
        return await self._get_resolver_data(ctx, body)

    async def _get_resolver_data(self, ctx: IExecutionContext, body: t.Any) -> t.Tuple:
        values: t.Dict[str, t.Any] = {}
        errors: t.List[ErrorWrapper] = []
        for parameter_resolver in self._resolvers:
            value_, errors_ = await parameter_resolver.resolve(ctx=ctx, body=body)
            if value_:
                values.update(value_)
            if errors_:
                errors += self.validate_error_sequence(errors_)
        return values, errors

    async def resolve_handle(
        self, ctx: IExecutionContext, *args: t.Any, **kwargs: t.Any
    ) -> t.Tuple:
        request_logger.debug(f"Resolving Form Parameters - '{self.__class__.__name__}'")
        _body = await self.get_request_body(ctx)
        if self._resolvers:
            return await self._use_resolver(ctx, _body)
        return await super(BulkFormParameterResolver, self).resolve_handle(
            ctx, *args, **kwargs
        )


class BulkBodyParameterResolver(BodyParameterResolver, BulkParameterResolver):
    async def resolve_handle(
        self, ctx: IExecutionContext, *args: t.Any, **kwargs: t.Any
    ) -> t.Tuple:
        request_logger.debug(
            f"Resolving Request Body Parameters - '{self.__class__.__name__}'"
        )
        _body = await self.get_request_body(ctx)
        values, errors = await super(BulkBodyParameterResolver, self).resolve_handle(
            ctx, *args, body=_body, **kwargs
        )
        if not errors:
            _, body_value = values.popitem()
            return body_value.dict(), []
        return values, self.validate_error_sequence(errors)
