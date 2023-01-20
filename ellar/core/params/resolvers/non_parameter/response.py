import typing as t

from ellar.core.context import IExecutionContext

from .base import NonParameterResolver


class ResponseRequestParam(NonParameterResolver):
    async def resolve(
        self, ctx: IExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.List]:
        response = ctx.switch_to_http_connection().get_response()
        return {self.parameter_name: response}, []
