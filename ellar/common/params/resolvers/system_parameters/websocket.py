import typing as t

from ellar.common.interfaces import IExecutionContext
from ellar.common.params.resolvers.base import ResolverResult

from .base import SystemParameterResolver


class WebSocketParameter(SystemParameterResolver):
    async def resolve(self, ctx: IExecutionContext, **kwargs: t.Any) -> ResolverResult:
        websocket = ctx.switch_to_websocket().get_client()
        return ResolverResult(
            {self.parameter_name: websocket}, [], self.create_raw_data(websocket)
        )
