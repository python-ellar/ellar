import inspect
import re
from typing import Callable, Set, List, Mapping, Tuple, Any, Dict, Union, cast, TYPE_CHECKING, Type, Optional
from pydantic.error_wrappers import ErrorWrapper
from pydantic import BaseModel
from pydantic.fields import (
    SHAPE_SINGLETON,
    FieldInfo,
    ModelField,
    Required
)

from pydantic.schema import SHAPE_SINGLETON, get_annotation_from_field_info
from pydantic.utils import lenient_issubclass

from pydantic.typing import evaluate_forwardref, ForwardRef

from starletteapi.constants import sequence_types
from starletteapi.context import ExecutionContext
from .helpers import create_response_field
from .param_resolvers import NonFieldRouteParameter, ParameterResolver, BodyParameterResolver
from . import params

if TYPE_CHECKING:
    from starletteapi.routing.operations import ExtraOperationArgs


def is_scalar_field(field: ModelField) -> bool:
    field_info = field.field_info
    if not (
            field.shape == SHAPE_SINGLETON
            and not lenient_issubclass(field.type_, BaseModel)
            and not lenient_issubclass(field.type_, sequence_types + (dict,))
            # and not dataclasses.is_dataclass(field.type_)
            and not isinstance(field_info, params.Body)
    ):
        return False
    if field.sub_fields:
        if not all(is_scalar_field(f) for f in field.sub_fields):
            return False
    return True


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


class RouteParameterModel:
    def __init__(self, *, path: str, endpoint: Callable):
        self.path = path
        self.body_resolvers = []
        self.path_param_names = self.get_path_param_names(path)
        endpoint_signature = self.get_typed_signature(endpoint)
        self.models: List[Union[NonFieldRouteParameter, params.Param]] = []
        self.compute_route_parameter_list(endpoint_signature.parameters)
        self.compute_body_resolvers()

    def compute_body_resolvers(self):
        body_resolvers = [
            resolver
            for resolver in self.models
            if isinstance(resolver, BodyParameterResolver)
        ]
        if len(body_resolvers) > 1:
            for resolver in body_resolvers:
                setattr(resolver.model_field.field_info, 'embed', True)
        self.body_resolvers = body_resolvers

    def compute_route_parameter_list(self, signature_params: Mapping[str, inspect.Parameter]) -> None:
        for param_name, param in signature_params.items():
            if param.kind == param.VAR_KEYWORD or param.kind == param.VAR_POSITIONAL or (param.name == 'self' and param.annotation == inspect.Parameter.empty):
                # Skipping **kwargs, *args, self
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
        if isinstance(param.default, NonFieldRouteParameter):
            _model = cast(NonFieldRouteParameter, param.default)
            model = _model(param.name, param.annotation)
            self.models.append(model)
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
        self.models.append(field_info.get_resolver())

    async def resolve_dependencies(
            self,
            *,
            ctx: ExecutionContext
    ) -> Tuple[Dict[str, Any], List[ErrorWrapper]]:
        values: Dict[str, Any] = {}
        errors: List[ErrorWrapper] = []
        for parameter_resolver in self.models:
            parameter_resolver = cast(ParameterResolver, parameter_resolver)
            value_, errors_ = await parameter_resolver.resolve(ctx=ctx)
            if value_:
                values.update(value_)
            errors += errors_
        return values, errors

    def add_extra_route_args(self, *extra_operation_args: 'ExtraOperationArgs') -> None:
        for param in extra_operation_args:
            if isinstance(param.default, NonFieldRouteParameter):
                _model = cast(NonFieldRouteParameter, param.default)
                model = _model(param.name, param.annotation)
                self.models.append(model)
                continue

            default_field_info = param.default if isinstance(param.default, FieldInfo) else params.Query
            param_field = get_parameter_field(
                param=cast(inspect.Parameter, param),
                default_field_info=default_field_info,
                param_name=param.name
            )
            self.add_to_model(field=param_field)

        self.compute_body_resolvers()

