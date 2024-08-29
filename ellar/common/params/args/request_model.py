import typing as t

from ellar.common.constants import MULTI_RESOLVER_KEY
from ellar.common.interfaces import IExecutionContext
from ellar.common.logging import logger
from ellar.pydantic import (
    BaseModel,
    ModelField,
    create_body_model,
    create_model_field,
)
from starlette.convertors import Convertor

from .. import params
from ..resolvers import (
    BodyParameterResolver,
    BulkFormParameterResolver,
    IRouteParameterResolver,
    RouteParameterModelField,
)
from ..resolvers.base import ResolverResult
from .base import EndpointArgsModel
from .extra_args import ExtraEndpointArg

multipart_not_installed_error = (
    'Form data requires "python-multipart" to be installed. \n'
    'You can install "python-multipart" with: \n\n'
    "pip install python-multipart\n"
)
multipart_incorrect_install_error = (
    'Form data requires "python-multipart" to be installed. '
    'It seems you installed "multipart" instead. \n'
    'You can remove "multipart" with: \n\n'
    "pip uninstall multipart\n\n"
    'And then install "python-multipart" with: \n\n'
    "pip install python-multipart\n"
)


def check_file_field(field: t.Any) -> None:
    field_info = field.field_info
    if isinstance(field_info, params.FormFieldInfo):
        try:
            # __version__ is available in both multiparts, and can be mocked
            from multipart import __version__

            assert __version__
            try:
                # parse_options_header is only available in the right multipart
                from multipart.multipart import parse_options_header

                assert parse_options_header
            except ImportError:
                logger.error(multipart_incorrect_install_error)
                raise RuntimeError(multipart_incorrect_install_error) from None
        except ImportError:
            logger.error(multipart_not_installed_error)
            raise RuntimeError(multipart_not_installed_error) from None


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
        extra_endpoint_args: t.Optional[t.Sequence[ExtraEndpointArg]] = None,
    ) -> None:
        super().__init__(
            path=path,
            endpoint=endpoint,
            param_converters=param_converters,
            extra_endpoint_args=extra_endpoint_args,
        )
        self.operation_unique_id = operation_unique_id

    def _get_body_resolver_model_fields(
        self, body_resolvers: t.List[IRouteParameterResolver]
    ) -> t.Generator[t.Union["RouteParameterModelField", ModelField], t.Any, None]:
        for resolver in body_resolvers:
            if isinstance(resolver, BulkFormParameterResolver):
                for form_resolver in resolver.resolvers:
                    yield form_resolver.model_field
            else:
                yield resolver.model_field

    def build_body_field(self) -> None:
        """
        Group common body / form fields to one field
        :return:
        """
        self.body_resolver = None

        body_resolvers = self._computation_models[params.BodyFieldInfo.in_.value]
        if (
            body_resolvers
            and len(body_resolvers) == 1
            and not isinstance(body_resolvers[0], BulkFormParameterResolver)
            and (
                isinstance(body_resolvers[0], BodyParameterResolver)
                and not body_resolvers[0].model_field.field_info.embed  # type: ignore[attr-defined]
            )
        ):
            check_file_field(body_resolvers[0].model_field)
            self.body_resolver = body_resolvers[0]
        elif body_resolvers:
            # if body_resolvers is more than one, we create a bulk_body_resolver instead
            model_name = "body_" + self.operation_unique_id
            _fields_required, _body_param_class, _fields = [], {}, []

            for f in self._get_body_resolver_model_fields(body_resolvers):
                f.field_info.embed = True  # type:ignore[attr-defined]
                _fields.append(f)
                _fields_required.append(f.required)
                _body_param_class[
                    getattr(f.field_info, "media_type", "application/json")
                ] = (f.field_info.__class__, f.field_info)

            pydantic_body_model: t.Type[BaseModel] = create_body_model(
                fields=_fields, model_name=model_name
            )

            required = any(_fields_required)
            body_field_info: t.Union[
                t.Type[params.BodyFieldInfo], t.Type[params.ParamFieldInfo]
            ] = params.BodyFieldInfo
            media_type = "application/json"

            field_info_kwargs: t.Dict[str, t.Any] = {
                "annotation": pydantic_body_model,
                "alias": "body",
                "media_type": media_type,
                MULTI_RESOLVER_KEY: body_resolvers,
            }

            if not required:
                field_info_kwargs["default"] = None

            if len(_body_param_class) == 1:
                _, (klass, field_info) = _body_param_class.popitem()
                body_field_info = klass  # type:ignore[assignment]
                field_info_kwargs["media_type"] = getattr(
                    field_info, "media_type", media_type
                )
            elif len(_body_param_class) > 1:
                key = sorted(_body_param_class.keys(), reverse=True)[0]
                klass, field_info = _body_param_class[key]
                body_field_info = klass  # type:ignore[assignment]
                field_info_kwargs["media_type"] = getattr(
                    field_info, "media_type", media_type
                )

            final_field = create_model_field(
                name="body",
                type_=pydantic_body_model,
                field_info=body_field_info(**field_info_kwargs, ellar_body=True),
            )
            final_field.field_info = t.cast(
                params.ParamFieldInfo, final_field.field_info
            )
            check_file_field(final_field)
            self.body_resolver = final_field.field_info.create_resolver(final_field)

    async def resolve_body(self, ctx: IExecutionContext) -> ResolverResult:
        if not self.body_resolver:
            return ResolverResult({}, [], {})

        return await self.body_resolver.resolve(ctx=ctx)
