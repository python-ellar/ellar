import typing as t

from pydantic.error_wrappers import ErrorWrapper

from ellar.core.context import IExecutionContext

from .base import NonParameterResolver


class WebSocketParameter(NonParameterResolver):
    async def resolve(
        self, ctx: IExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.List]:
        try:
            websocket = ctx.switch_to_websocket().get_client()
            return {self.parameter_name: websocket}, []
        except Exception as ex:
            return {}, [ErrorWrapper(ex, loc=self.parameter_name or "websocket")]
