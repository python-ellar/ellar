import typing as t

from ellar.common.interfaces import IExecutionContext
from ellar.common.params.resolvers.base import ResolverResult

from .base import SystemParameterResolver


class ExecutionContextParameter(SystemParameterResolver):
    async def resolve(self, ctx: IExecutionContext, **kwargs: t.Any) -> ResolverResult:
        return ResolverResult({self.parameter_name: ctx}, [], self.create_raw_data(ctx))
