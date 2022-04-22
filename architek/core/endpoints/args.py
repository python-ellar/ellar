import inspect
import re
import typing as t

from pydantic import BaseModel, create_model
from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import FieldInfo, ModelField, Required
from pydantic.schema import get_annotation_from_field_info
from pydantic.typing import ForwardRef, evaluate_forwardref

from architek.core.connection import Request, WebSocket
from architek.core.context import ExecutionContext
from architek.core.helper.modelfield import create_model_field
from architek.types import T

from . import params
from .helpers import is_scalar_field
from .resolvers import (
    BaseRouteParameterResolver,
    BodyParameterResolver,
    NonFieldRouteParameterResolver,
    ParameterInjectable,
    RouteParameterResolver,
    WsBodyParameterResolver,
)

__all__ = [
    "ExtraEndpointArg",
    "RequestEndpointArgsModel",
    "WebsocketEndpointArgsModel",
    "EndpointArgsModel",
]


def get_parameter_field(
    *,
    param: inspect.Parameter,
    param_name: str,
    default_field_info: t.Type[params.Param] = params.Param,
    ignore_default: bool = False,
    body_field_class: t.Type[FieldInfo] = params.Body,
) -> ModelField:
    default_value = Required
    had_schema = False
    if param.default is not param.empty and ignore_default is False:
        default_value = param.default

    if isinstance(default_value, FieldInfo):
        had_schema = True
        field_info = default_value
        default_value = field_info.default
        if (
            isinstance(field_info, params.Param)
            and getattr(field_info, "in_", None) is None
        ):
            field_info.in_ = default_field_info.in_
    else:
        field_info = default_field_info(default_value)

    required = default_value == Required
    annotation: t.Any = t.Any

    if not field_info.alias and getattr(field_info, "convert_underscores", None):
        alias = param.name.replace("_", "-")
    else:
        alias = field_info.alias or param.name

    if not param.annotation == param.empty:
        annotation = param.annotation

    field = create_model_field(
        name=param.name,
        type_=get_annotation_from_field_info(annotation, field_info, param_name),
        default=None if required else default_value,
        alias=alias,
        required=required,
        field_info=field_info,
    )
    field.required = required

    if not had_schema and not is_scalar_field(field=field):
        field.field_info = body_field_class(field_info.default)

    field_info = t.cast(params.Param, field.field_info)
    field_info.init_resolver(field)

    return field


class ExtraEndpointArg(t.Generic[T]):
    __slots__ = ("name", "annotation", "default")

    empty = inspect.Parameter.empty

    def __init__(
        self, *, name: str, annotation: t.Type[T], default_value: t.Any = None
    ):
        self.name = name
        self.annotation = annotation
        self.default = default_value or self.empty

    def resolve(self, kwargs: t.Dict) -> T:
        if self.name in kwargs:
            return t.cast(T, kwargs.pop(self.name))
        raise AttributeError(f"{self.name} ExtraOperationArg not found")


class EndpointArgsModel:
    __slots__ = (
        "path",
        "_models",
        "path_param_names",
        "body_resolver",
        "endpoint_signature",
    )

    def __init__(
        self,
        *,
        path: str,
        endpoint: t.Callable,
    ) -> None:
        self.path = path
        self._models: t.List[BaseRouteParameterResolver] = []
        self.path_param_names = self.get_path_param_names(path)
        self.endpoint_signature = self.get_typed_signature(endpoint)
        self.body_resolver: t.Optional[RouteParameterResolver] = None

    def get_models(self) -> t.List[BaseRouteParameterResolver]:
        return list(self._models)

    def build_model(self) -> None:
        self.compute_route_parameter_list()
        self.build_body_field()

    def compute_route_parameter_list(
        self, body_field_class: t.Type[FieldInfo] = params.Body
    ) -> None:
        for param_name, param in self.endpoint_signature.parameters.items():
            if (
                param.kind == param.VAR_KEYWORD
                or param.kind == param.VAR_POSITIONAL
                or (
                    param.name == "self" and param.annotation == inspect.Parameter.empty
                )
            ):
                # Skipping **kwargs, *args, self
                continue
            if param_name == "request" and param.default == inspect.Parameter.empty:
                self._models.append(ParameterInjectable()(param_name, Request))
                continue

            if param_name == "websocket" and param.default == inspect.Parameter.empty:
                self._models.append(ParameterInjectable()(param_name, WebSocket))
                continue

            if self.add_non_field_param_to_dependency(param=param):
                continue

            default_field_info = t.cast(
                t.Type[params.Param],
                param.default if isinstance(param.default, FieldInfo) else params.Query,
            )
            param_field = get_parameter_field(
                param=param,
                default_field_info=default_field_info,
                param_name=param_name,
                body_field_class=body_field_class,
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
    ) -> t.Optional[bool]:
        if isinstance(param.default, NonFieldRouteParameterResolver):
            _model = param.default
            model = _model(param.name, param.annotation)
            self._models.append(model)
            return True
        return None

    @classmethod
    def get_path_param_names(cls, path: str) -> t.Set[str]:
        return set(re.findall("{(.*?)}", path))

    @classmethod
    def get_typed_signature(cls, call: t.Callable[..., t.Any]) -> inspect.Signature:
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
    def get_typed_annotation(
        cls, param: inspect.Parameter, globalns: t.Dict[str, t.Any]
    ) -> t.Any:
        annotation = param.annotation
        if isinstance(annotation, str):
            annotation = ForwardRef(annotation)
            annotation = evaluate_forwardref(annotation, globalns, globalns)
        return annotation

    def add_to_model(self, *, field: ModelField) -> None:
        field_info = t.cast(params.Param, field.field_info)
        self._models.append(field_info.get_resolver())

    async def resolve_dependencies(
        self, *, ctx: ExecutionContext
    ) -> t.Tuple[t.Dict[str, t.Any], t.List[ErrorWrapper]]:
        values: t.Dict[str, t.Any] = {}
        errors: t.List[ErrorWrapper] = []

        if self.body_resolver:
            await self.resolve_body(ctx, values, errors)

        if not errors:
            for parameter_resolver in self._models:
                value_, value_errors = await parameter_resolver.resolve(ctx=ctx)
                if value_:
                    values.update(value_)
                if value_errors:
                    _errors = (
                        value_errors
                        if isinstance(value_errors, list)
                        else [value_errors]
                    )
                    errors += _errors
        return values, errors

    def add_extra_route_args(self, *extra_operation_args: ExtraEndpointArg) -> None:
        for param in extra_operation_args:
            if isinstance(param.default, NonFieldRouteParameterResolver):
                model = param.default(param.name, param.annotation)
                self._models.append(model)
                continue

            default_field_info = t.cast(
                t.Type[params.Param],
                param.default if isinstance(param.default, FieldInfo) else params.Query,
            )
            param_field = get_parameter_field(
                param=t.cast(inspect.Parameter, param),
                default_field_info=default_field_info,
                param_name=param.name,
            )
            self.add_to_model(field=param_field)

    async def resolve_body(
        self, ctx: ExecutionContext, values: t.Dict, errors: t.List
    ) -> None:
        ...

    def __deepcopy__(self, memodict: t.Dict = {}) -> "EndpointArgsModel":
        return self.__copy__(memodict)

    def __copy__(self, memodict: t.Dict = {}) -> "EndpointArgsModel":
        return self

    def build_body_field(self) -> None:
        raise NotImplementedError


class RequestEndpointArgsModel(EndpointArgsModel):
    __slots__ = ("operation_unique_id", "body_resolvers")

    def __init__(
        self, *, path: str, endpoint: t.Callable, operation_unique_id: str
    ) -> None:
        super().__init__(path=path, endpoint=endpoint)
        self.operation_unique_id = operation_unique_id

    def _compute_body_resolvers(self) -> t.List[BodyParameterResolver]:
        body_resolvers = []
        for resolver in list(self._models):
            if isinstance(resolver, BodyParameterResolver):
                body_resolvers.append(resolver)
                self._models.remove(resolver)

        if len(body_resolvers) > 1:
            for resolver in body_resolvers:
                setattr(resolver.model_field.field_info, "embed", True)
        return body_resolvers

    def build_body_field(self) -> None:
        self.body_resolver = None

        body_resolvers = self._compute_body_resolvers()
        if body_resolvers and len(body_resolvers) == 1:
            self.body_resolver = body_resolvers[0]
            return

        if body_resolvers:
            _body_resolvers_model_fields = [item.model_field for item in body_resolvers]
            model_name = "body_" + self.operation_unique_id
            body_model_field: t.Type[BaseModel] = create_model(model_name)
            _fields_required, _body_param_class = [], dict()
            for f in _body_resolvers_model_fields:
                body_model_field.__fields__[f.name] = f
                _fields_required.append(f.required)
                _body_param_class[f.field_info.__class__] = f.field_info

            required = any(_fields_required)
            body_field_info: t.Union[
                t.Type[params.Body], t.Type[params.Param]
            ] = params.Body
            media_type = "application/json"
            if len(_body_param_class) == 1:
                klass, field_info = _body_param_class.popitem()
                body_field_info = klass
                media_type = getattr(field_info, "media_type", media_type)

            final_field = create_model_field(
                name="body",
                type_=body_model_field,
                required=required,
                alias="body",
                field_info=body_field_info(
                    media_type=media_type, default=None, body_resolvers=body_resolvers
                ),
            )
            final_field.field_info = t.cast(params.Param, final_field.field_info)
            final_field.field_info.init_resolver(final_field)
            self.body_resolver = final_field.field_info.get_resolver()

    async def resolve_body(
        self, ctx: ExecutionContext, values: t.Dict, errors: t.List
    ) -> None:
        if not self.body_resolver:
            return

        body, errors_ = await self.body_resolver.resolve(ctx=ctx)
        if errors_:
            errors += list(errors_ if isinstance(errors_, list) else [errors_])
            return
        values.update(body)


class WebsocketEndpointArgsModel(EndpointArgsModel):
    __slots__ = ("body_resolvers",)

    def __init__(self, *, path: str, endpoint: t.Callable) -> None:
        super().__init__(path=path, endpoint=endpoint)
        self.body_resolvers: t.List[RouteParameterResolver] = []

    def build_body_field(self) -> None:
        for resolver in list(self._models):
            if isinstance(resolver, WsBodyParameterResolver):
                self.body_resolvers.append(resolver)
                self._models.remove(resolver)

        if len(self.body_resolvers) > 1:
            for resolver in self.body_resolvers:
                setattr(resolver.model_field.field_info, "embed", True)

    def compute_route_parameter_list(
        self, body_field_class: t.Type[FieldInfo] = params.Body
    ) -> None:
        super().compute_route_parameter_list(body_field_class=params.WsBody)

    async def resolve_ws_body_dependencies(
        self, *, ctx: ExecutionContext, body_data: t.Any
    ) -> t.Tuple[t.Dict[str, t.Any], t.List[ErrorWrapper]]:
        values: t.Dict[str, t.Any] = {}
        errors: t.List[ErrorWrapper] = []
        for parameter_resolver in self.body_resolvers:
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
