import typing as t

from ellar.common.interfaces import IExecutionContext

from .base import SystemParameterResolver


class ExecutionContextParameter(SystemParameterResolver):
    async def resolve(
        self, ctx: IExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.List]:
        return {self.parameter_name: ctx}, []
