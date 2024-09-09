import typing as t

from ellar.common.interfaces import IExecutionContext
from ellar.common.params.resolvers.base import ResolverResult

from .base import SystemParameterResolver


class ConnectionParam(SystemParameterResolver):
    async def resolve(self, ctx: IExecutionContext, **kwargs: t.Any) -> ResolverResult:
        connection = ctx.switch_to_http_connection().get_client()
        return ResolverResult(
            {self.parameter_name: connection}, [], self.create_raw_data(connection)
        )
