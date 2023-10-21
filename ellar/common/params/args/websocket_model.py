import typing as t

from ellar.common.interfaces import IExecutionContext
from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import FieldInfo
from starlette.convertors import Convertor

from .. import params
from ..resolvers import BaseRouteParameterResolver, WsBodyParameterResolver
from .base import EndpointArgsModel
from .extra_args import ExtraEndpointArg


class WebsocketEndpointArgsModel(EndpointArgsModel):
    body_resolver: t.List[BaseRouteParameterResolver]

    def __init__(
        self,
        *,
        path: str,
        endpoint: t.Callable,
        param_converters: t.Dict[str, Convertor],
        extra_endpoint_args: t.Optional[t.Sequence[ExtraEndpointArg]] = None,
    ) -> None:
        super().__init__(
            path=path,
            endpoint=endpoint,
            param_converters=param_converters,
            extra_endpoint_args=extra_endpoint_args,
        )
        self.body_resolver = []

    def build_body_field(self) -> None:
        for resolver in list(self._computation_models[params.BodyFieldInfo.in_.value]):
            if isinstance(resolver, WsBodyParameterResolver):
                self.body_resolver.append(resolver)
                self._computation_models[
                    resolver.model_field.field_info.in_.value
                ].remove(resolver)

        if self.body_resolver and len(self.body_resolver) > 1:
            for resolver in self.body_resolver:
                resolver.model_field.field_info.embed = (  # type:ignore[attr-defined]
                    True
                )

    def compute_route_parameter_list(
        self, body_field_class: t.Type[FieldInfo] = params.BodyFieldInfo
    ) -> None:
        super().compute_route_parameter_list(body_field_class=params.WsBodyFieldInfo)

    async def resolve_ws_body_dependencies(
        self, *, ctx: IExecutionContext, body_data: t.Any
    ) -> t.Tuple[t.Dict[str, t.Any], t.List[ErrorWrapper]]:
        values: t.Dict[str, t.Any] = {}
        errors: t.List[ErrorWrapper] = []
        for parameter_resolver in self.body_resolver or []:
            parameter_resolver = t.cast(WsBodyParameterResolver, parameter_resolver)
            value_, errors_ = await parameter_resolver.resolve(ctx=ctx, body=body_data)
            if value_:
                values.update(value_)
            if errors_:
                if isinstance(errors_, list):
                    errors += errors_
                else:
                    errors.append(errors_)
        return values, errors
