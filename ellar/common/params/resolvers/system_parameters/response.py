import typing as t

from ellar.common.interfaces import IExecutionContext
from ellar.common.params.resolvers.base import ResolverResult

from .base import SystemParameterResolver


class ResponseRequestParam(SystemParameterResolver):
    async def resolve(self, ctx: IExecutionContext, **kwargs: t.Any) -> ResolverResult:
        response = ctx.switch_to_http_connection().get_response()
        return ResolverResult(
            {self.parameter_name: response}, [], self.create_raw_data(response)
        )
