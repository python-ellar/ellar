import typing as t

from pydantic.error_wrappers import ErrorWrapper

from ellar.core.context import IExecutionContext

from .base import NonParameterResolver


class ResponseRequestParam(NonParameterResolver):
    async def resolve(
        self, ctx: IExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.List]:
        try:
            response = ctx.switch_to_http_connection().get_response()
            return {self.parameter_name: response}, []
        except Exception as ex:
            return {}, [ErrorWrapper(ex, loc=self.parameter_name or "response")]
