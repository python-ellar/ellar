import typing as t

from ellar.core.context import IExecutionContext

from .base import NonParameterResolver


class ConnectionParam(NonParameterResolver):
    async def resolve(
        self, ctx: IExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.List]:
        connection = ctx.switch_to_http_connection().get_client()
        return {self.parameter_name: connection}, []
