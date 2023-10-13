import typing as t

from ellar.common.interfaces import IExecutionContext

from .base import SystemParameterResolver


class ResponseRequestParam(SystemParameterResolver):
    async def resolve(
        self, ctx: IExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.List]:
        response = ctx.switch_to_http_connection().get_response()
        return {self.parameter_name: response}, []
