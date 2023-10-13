import typing as t

from ellar.common.interfaces import IExecutionContext

from .base import SystemParameterResolver


class RequestParameter(SystemParameterResolver):
    async def resolve(
        self, ctx: IExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.List]:
        request = ctx.switch_to_http_connection().get_request()
        return {self.parameter_name: request}, []
