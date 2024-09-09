import typing as t

from ellar.common.interfaces import IExecutionContext
from ellar.common.params.resolvers.base import ResolverResult

from .base import SystemParameterResolver


class RequestParameter(SystemParameterResolver):
    async def resolve(self, ctx: IExecutionContext, **kwargs: t.Any) -> ResolverResult:
        request = ctx.switch_to_http_connection().get_request()
        return ResolverResult(
            {self.parameter_name: request}, [], self.create_raw_data(request)
        )
