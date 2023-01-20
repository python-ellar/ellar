import typing as t

from ellar.core.context import IExecutionContext

from .base import NonParameterResolver


class WebSocketParameter(NonParameterResolver):
    async def resolve(
        self, ctx: IExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.List]:
        websocket = ctx.switch_to_websocket().get_client()
        return {self.parameter_name: websocket}, []
