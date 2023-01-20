import typing as t

from ellar.core.context import IExecutionContext

from .base import NonParameterResolver


class RequestParameter(NonParameterResolver):
    async def resolve(
        self, ctx: IExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.List]:
        request = ctx.switch_to_http_connection().get_request()
        return {self.parameter_name: request}, []
