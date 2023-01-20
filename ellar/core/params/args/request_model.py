import typing as t

from pydantic import BaseModel, create_model
from starlette.convertors import Convertor

from ellar.constants import MULTI_RESOLVER_KEY
from ellar.core.context import IExecutionContext
from ellar.helper.modelfield import create_model_field

from .. import params
from ..resolvers import BaseRouteParameterResolver
from .base import EndpointArgsModel
from .extra_args import ExtraEndpointArg


class RequestEndpointArgsModel(EndpointArgsModel):
    __slots__ = (
        "operation_unique_id",
        "path",
        "_computation_models",
        "path_param_names",
        "body_resolver",
        "endpoint_signature",
        "_route_models",
        "param_converters",
        "_extra_endpoint_args",
    )

    def __init__(
        self,
        *,
        path: str,
        endpoint: t.Callable,
        operation_unique_id: str,
        param_converters: t.Dict[str, Convertor],
        extra_endpoint_args: t.Sequence[ExtraEndpointArg] = None,
    ) -> None:
        super().__init__(
            path=path,
            endpoint=endpoint,
            param_converters=param_converters,
            extra_endpoint_args=extra_endpoint_args,
        )
        self.operation_unique_id = operation_unique_id

    def build_body_field(self) -> None:
        """
        Group common body / form fields to one field
        :return:
        """
        self.body_resolver = None

        body_resolvers = self._computation_models[params.Body.in_.value]
        if body_resolvers and len(body_resolvers) == 1:
            self.body_resolver = body_resolvers[0]
        elif body_resolvers:
            # if body_resolvers is more than one, we create a bulk_body_resolver instead
            _body_resolvers_model_fields = (
                t.cast(BaseRouteParameterResolver, item).model_field
                for item in body_resolvers
            )
            model_name = "body_" + self.operation_unique_id
            body_model_field: t.Type[BaseModel] = create_model(model_name)
            _fields_required, _body_param_class = [], dict()
            for f in _body_resolvers_model_fields:
                setattr(f.field_info, "embed", True)
                body_model_field.__fields__[f.alias or f.name] = f
                _fields_required.append(f.required)
                _body_param_class[
                    getattr(f.field_info, "media_type", "application/json")
                ] = (f.field_info.__class__, f.field_info)

            required = any(_fields_required)
            body_field_info: t.Union[
                t.Type[params.Body], t.Type[params.Param]
            ] = params.Body
            media_type = "application/json"
            if len(_body_param_class) == 1:
                _, (klass, field_info) = _body_param_class.popitem()
                body_field_info = klass
                media_type = getattr(field_info, "media_type", media_type)
            elif len(_body_param_class) > 1:
                key = list(reversed(sorted(_body_param_class.keys())))[0]
                klass, field_info = _body_param_class[key]
                body_field_info = klass
                media_type = getattr(field_info, "media_type", media_type)

            final_field = create_model_field(
                name="body",
                type_=body_model_field,
                required=required,
                alias="body",
                field_info=body_field_info(
                    media_type=media_type,
                    default=None,
                    **{MULTI_RESOLVER_KEY: body_resolvers},  # type:ignore
                ),
            )
            final_field.field_info = t.cast(params.Param, final_field.field_info)
            self.body_resolver = final_field.field_info.create_resolver(final_field)

    async def resolve_body(
        self, ctx: IExecutionContext, values: t.Dict, errors: t.List
    ) -> None:
        if not self.body_resolver:
            return

        body, errors_ = await self.body_resolver.resolve(ctx=ctx)
        if errors_:
            errors += list(errors_ if isinstance(errors_, list) else [errors_])
            return
        values.update(body)
