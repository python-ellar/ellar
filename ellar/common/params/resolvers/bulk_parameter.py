import typing as t

from ellar.common.interfaces import IExecutionContext
from ellar.common.logging import request_logger
from ellar.pydantic import ModelField

from .base import BaseRouteParameterResolver, ResolverResult
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
    ) -> ResolverResult:
        request_logger.debug(
            f"Resolving Bulk Path Parameters - '{self.__class__.__name__}'"
        )
        values: t.Dict[str, t.Any] = {}
        errors = []
        raw_data = {}

        for parameter_resolver in self._resolvers:
            res = await parameter_resolver.resolve(*args, ctx=ctx, **kwargs)
            if res.data:
                values.update(
                    {
                        parameter_resolver.model_field.alias: res.data[
                            parameter_resolver.model_field.name
                        ]
                    }
                )
            if res.errors:
                errors += self.validate_error_sequence(res.errors)

            raw_data.update(res.raw_data)

        if errors:
            return ResolverResult(values, errors=errors, raw_data=raw_data)

        # Combining resolved values into one pydantic model specified by the user in Route function parameter
        v_, errors_ = self.model_field.validate(
            values,
            {},
            loc=(self.model_field.field_info.in_.value, self.model_field.alias),
        )
        if errors_:  # pragma: no cover
            # Just in case error still happened after combining each field to one pydantic model.
            errors += self.validate_error_sequence(errors_)
            return ResolverResult(values, errors=errors, raw_data=raw_data)
        return ResolverResult({self.model_field.name: v_}, errors=[], raw_data=raw_data)


class BulkFormParameterResolver(FormParameterResolver, BulkParameterResolver):
    def __init__(self, *args: t.Any, is_grouped: bool = False, **kwargs: t.Any):
        super().__init__(*args, **kwargs)
        self.is_grouped = is_grouped
        self._use_resolver: t.Callable[
            [IExecutionContext, t.Any], t.Awaitable[ResolverResult]
        ] = t.cast(
            t.Callable[[IExecutionContext, t.Any], t.Awaitable[ResolverResult]],
            self.resolve_grouped_fields
            if is_grouped
            else self.resolve_ungrouped_fields,
        )

    async def resolve_grouped_fields(
        self, ctx: IExecutionContext, body: t.Any
    ) -> ResolverResult:
        request_logger.debug(
            f"Resolving Form Grouped Field - '{self.__class__.__name__}'"
        )
        res = await self._get_resolver_data(ctx, body, by_alias=True)
        if res.errors:
            return res
        # Combining resolved values into one pydantic model specified by the user in Route function parameter
        processed_value, processed_errors = self.model_field.validate(
            res.data,
            {},
            loc=(self.model_field.field_info.in_.value, self.model_field.alias),
        )

        if processed_errors:  # pragma: no cover
            # Just in case error still happened after combining each field to one pydantic model.
            processed_errors = self.validate_error_sequence(processed_errors)
            return ResolverResult(
                processed_value, processed_errors, raw_data=res.raw_data
            )
        return ResolverResult(
            {self.model_field.name: processed_value}, [], res.raw_data
        )

    async def resolve_ungrouped_fields(
        self, ctx: IExecutionContext, body: t.Any
    ) -> ResolverResult:
        return await self._get_resolver_data(ctx, body)

    async def _get_resolver_data(
        self, ctx: IExecutionContext, body: t.Any, by_alias: bool = False
    ) -> ResolverResult:
        values: t.Dict[str, t.Any] = {}
        errors = []
        raw_data = {}
        for parameter_resolver in self._resolvers:
            res_ = await parameter_resolver.resolve(ctx=ctx, body=body)
            if res_.data:
                value = (
                    res_.data
                    if not by_alias
                    else {
                        parameter_resolver.model_field.alias: res_.data[
                            parameter_resolver.model_field.name
                        ]
                    }
                )
                values.update(value)
            if res_.errors:
                errors += self.validate_error_sequence(res_.errors)
            raw_data.update(res_.raw_data)
        return ResolverResult(values, errors, raw_data)

    async def resolve_handle(
        self,
        ctx: IExecutionContext,
        *args: t.Any,
        body: t.Optional[t.Any] = None,
        **kwargs: t.Any,
    ) -> ResolverResult:
        request_logger.debug(f"Resolving Form Parameters - '{self.__class__.__name__}'")
        _body = body or await self.get_request_body(ctx)
        return await self._use_resolver(ctx, _body)


class BulkBodyParameterResolver(BulkParameterResolver, BodyParameterResolver):
    async def resolve_handle(
        self, ctx: IExecutionContext, *args: t.Any, **kwargs: t.Any
    ) -> ResolverResult:
        request_logger.debug(
            f"Resolving Request Body Parameters - '{self.__class__.__name__}'"
        )
        _body = await self.get_request_body(ctx)

        res = await super().resolve_handle(ctx, *args, body=_body, **kwargs)

        if res.errors:
            return ResolverResult(
                res.data, self.validate_error_sequence(res.errors), res.raw_data
            )

        # TODO: resolve to raw values. Remove extra loop
        _, body_value = res.data.popitem()
        return ResolverResult(
            {k: getattr(body_value, k) for k in body_value.model_fields_set},
            [],
            res.raw_data,
        )
