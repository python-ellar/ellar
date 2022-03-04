import inspect
import re
from typing import Callable, Set, List, Mapping, Tuple, Any, Dict, cast, TYPE_CHECKING, Type, Optional
from pydantic.error_wrappers import ErrorWrapper
from pydantic import BaseModel, create_model
from pydantic.fields import (
    FieldInfo,
    ModelField,
    Required
)

from pydantic.schema import get_annotation_from_field_info

from pydantic.typing import evaluate_forwardref, ForwardRef
from starletteapi.context import ExecutionContext
from .helpers import create_response_field, is_scalar_field
from .param_resolvers import (
    NonFieldRouteParameterResolver, BaseRouteParameterResolver,
    BodyParameterResolver, RouteParameterResolver, ParameterInjectable
)
from . import params
from ..websockets import WebSocket
from ..requests import Request

if TYPE_CHECKING:
    from starletteapi.routing.operations import ExtraOperationArgs


def get_parameter_field(
        *,
        param: inspect.Parameter,
        param_name: str,
        default_field_info: Type[params.Param] = params.Param,
        ignore_default: bool = False,
) -> ModelField:
    default_value = Required
    had_schema = False
    if param.default is not param.empty and ignore_default is False:
        default_value = param.default

    if isinstance(default_value, FieldInfo):
        had_schema = True
        field_info = default_value
        default_value = field_info.default
        if isinstance(field_info, params.Param) and getattr(field_info, "in_", None) is None:
            field_info.in_ = default_field_info.in_
    else:
        field_info = default_field_info(default_value)

    required = default_value == Required
    annotation: Any = Any

    if not field_info.alias and getattr(field_info, "convert_underscores", None):
        alias = param.name.replace("_", "-")
    else:
        alias = field_info.alias or param.name

    if not param.annotation == param.empty:
        annotation = param.annotation

    field = create_response_field(
        name=param.name,
        type_=get_annotation_from_field_info(annotation, field_info, param_name),
        default=None if required else default_value,
        alias=alias,
        required=required,
        field_info=field_info,
    )
    field.required = required

    if not had_schema and not is_scalar_field(field=field):
        field.field_info = params.Body(field_info.default)

    field_info = cast(params.Param, field.field_info)
    field_info.init_resolver(field)

    return field


class EndpointParameterModel:
    def __init__(self, *, path: str, endpoint: Callable,):
        self.path = path
        self._models: List[BaseRouteParameterResolver] = []
        self.path_param_names = self.get_path_param_names(path)
        endpoint_signature = self.get_typed_signature(endpoint)
        self.compute_route_parameter_list(endpoint_signature.parameters)
        self.body_resolver: Optional[RouteParameterResolver] = None

    def get_models(self) -> List[BaseRouteParameterResolver]:
        return list(self._models)

    def compute_route_parameter_list(self, signature_params: Mapping[str, inspect.Parameter]) -> None:
        for param_name, param in signature_params.items():
            if param.kind == param.VAR_KEYWORD or param.kind == param.VAR_POSITIONAL or (
                    param.name == 'self' and param.annotation == inspect.Parameter.empty
            ):
                # Skipping **kwargs, *args, self
                continue
            if param_name == 'request' and param.default == inspect.Parameter.empty:
                self._models.append(ParameterInjectable()(param_name, Request))
                continue

            if param_name == 'websocket' and param.default == inspect.Parameter.empty:
                self._models.append(ParameterInjectable()(param_name, WebSocket))
                continue

            if self.add_non_field_param_to_dependency(param=param):
                continue

            default_field_info = param.default if isinstance(param.default, FieldInfo) else params.Query
            param_field = get_parameter_field(
                param=param, default_field_info=default_field_info, param_name=param_name
            )
            if param_name in self.path_param_names:
                assert is_scalar_field(
                    field=param_field
                ), "Path params must be of one of the supported types"
                if isinstance(param.default, params.Path):
                    ignore_default = False
                else:
                    ignore_default = True
                param_field = get_parameter_field(
                    param=param,
                    param_name=param_name,
                    default_field_info=params.Path,
                    ignore_default=ignore_default,
                    # force_type=params.ParamTypes.path,
                )
            self.add_to_model(field=param_field)

    def add_non_field_param_to_dependency(
            self, *, param: inspect.Parameter
    ) -> Optional[bool]:
        if isinstance(param.default, NonFieldRouteParameterResolver):
            _model = cast(NonFieldRouteParameterResolver, param.default)
            model = _model(param.name, param.annotation)
            self._models.append(model)
            return True
        return None

    @classmethod
    def get_path_param_names(cls, path) -> Set[str]:
        return set(re.findall("{(.*?)}", path))

    @classmethod
    def get_typed_signature(cls, call: Callable[..., Any]) -> inspect.Signature:
        signature = inspect.signature(call)
        global_ns = getattr(call, "__globals__", {})
        typed_params = [
            inspect.Parameter(
                name=param.name,
                kind=param.kind,
                default=param.default,
                annotation=cls.get_typed_annotation(param, global_ns),
            )
            for param in signature.parameters.values()
        ]
        typed_signature = inspect.Signature(typed_params)
        return typed_signature

    @classmethod
    def get_typed_annotation(cls, param: inspect.Parameter, globalns: Dict[str, Any]) -> Any:
        annotation = param.annotation
        if isinstance(annotation, str):
            annotation = ForwardRef(annotation)
            annotation = evaluate_forwardref(annotation, globalns, globalns)
        return annotation

    def add_to_model(self, *, field: ModelField) -> None:
        field_info = cast(params.Param, field.field_info)
        self._models.append(field_info.get_resolver())

    async def resolve_dependencies(
            self,
            *,
            ctx: ExecutionContext
    ) -> Tuple[Dict[str, Any], List[ErrorWrapper]]:
        values: Dict[str, Any] = {}
        errors: List[ErrorWrapper] = []
        for parameter_resolver in self._models:
            parameter_resolver = cast(BaseRouteParameterResolver, parameter_resolver)
            value_, errors_ = await parameter_resolver.resolve(ctx=ctx)
            if value_:
                values.update(value_)
            if errors_:
                errors += errors_
        return values, errors

    def add_extra_route_args(self, *extra_operation_args: 'ExtraOperationArgs') -> None:
        for param in extra_operation_args:
            if isinstance(param.default, NonFieldRouteParameterResolver):
                _model = cast(NonFieldRouteParameterResolver, param.default)
                model = _model(param.name, param.annotation)
                self._models.append(model)
                continue

            default_field_info = param.default if isinstance(param.default, FieldInfo) else params.Query
            param_field = get_parameter_field(
                param=cast(inspect.Parameter, param),
                default_field_info=default_field_info,
                param_name=param.name
            )
            self.add_to_model(field=param_field)


class APIEndpointParameterModel(EndpointParameterModel):
    def __init__(self, *, path: str, endpoint: Callable, operation_unique_id: str):
        super().__init__(path=path, endpoint=endpoint)
        self.operation_unique_id = operation_unique_id
        self.build_endpoint_body_field()

    def _compute_body_resolvers(self):
        body_resolvers = [
            resolver
            for resolver in self._models
            if isinstance(resolver, BodyParameterResolver)
        ]
        if len(body_resolvers) > 1:
            for resolver in body_resolvers:
                setattr(resolver.model_field.field_info, 'embed', True)
        return body_resolvers

    def add_extra_route_args(self, *extra_operation_args: 'ExtraOperationArgs') -> None:
        super(APIEndpointParameterModel, self).add_extra_route_args(*extra_operation_args)
        self.build_endpoint_body_field()

    def build_endpoint_body_field(self):
        self.body_resolver = None
        
        body_resolvers = self._compute_body_resolvers()
        if body_resolvers and len(body_resolvers) == 1:
            self.body_resolver = body_resolvers[0]
            return
        if body_resolvers:
            _body_resolvers_model_fields = [item.model_field for item in body_resolvers]
            model_name = "body_" + self.operation_unique_id
            body_model_field: Type[BaseModel] = create_model(model_name)
            _fields_required, _body_param_class = [], dict()
            for f in _body_resolvers_model_fields:
                body_model_field.__fields__[f.name] = f
                _fields_required.append(f.required)
                _body_param_class[f.field_info.__class__] = f.field_info

            required = any(_fields_required)
            body_field_info = params.Body
            media_type = "application/json"
            if len(_body_param_class) == 1:
                klass, field_info = _body_param_class.popitem()
                body_field_info = klass
                media_type = getattr(field_info, 'media_type', media_type)

            final_field = create_response_field(
                name="body",
                type_=body_model_field,
                required=required,
                alias="body",
                field_info=body_field_info(media_type=media_type, default=None),
            )
            final_field.field_info.init_resolver(final_field)
            self.body_resolver = final_field.field_info.get_resolver()
