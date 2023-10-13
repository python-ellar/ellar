import typing as t

from ellar.common.interfaces import IExecutionContext

from .base import SystemParameterResolver


class ConnectionParam(SystemParameterResolver):
    async def resolve(
        self, ctx: IExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.List]:
        connection = ctx.switch_to_http_connection().get_client()
        return {self.parameter_name: connection}, []
