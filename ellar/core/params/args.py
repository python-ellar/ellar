import inspect
import re
import typing as t
from collections import defaultdict

from pydantic import BaseModel, create_model
from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import FieldInfo, ModelField, Required
from pydantic.schema import get_annotation_from_field_info
from pydantic.typing import ForwardRef, evaluate_forwardref
from pydantic.utils import lenient_issubclass
from starlette.convertors import Convertor

from ellar.constants import MULTI_RESOLVER_KEY, ROUTE_OPENAPI_PARAMETERS, sequence_types
from ellar.core.connection import Request, WebSocket
from ellar.core.context import IExecutionContext
from ellar.exceptions import ImproperConfiguration
from ellar.helper.modelfield import create_model_field
from ellar.types import T

from . import params
from .helpers import is_scalar_field, is_scalar_sequence_field
from .resolvers import (
    BaseRouteParameterResolver,
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
    param_default: t.Any,
    param_annotation: t.Type,
    param_name: str,
    default_field_info: t.Type[params.Param] = params.Param,
    ignore_default: bool = False,
    body_field_class: t.Type[FieldInfo] = params.Body,
) -> ModelField:

    default_value = Required
    had_schema = False
    if param_default is not inspect.Parameter.empty and ignore_default is False:
        default_value = param_default

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

    if not field_info.alias and getattr(
        field_info,
        "convert_underscores",
        getattr(field_info.extra, "convert_underscores", None),
    ):
        alias = param_name.replace("_", "-")
    else:
        alias = field_info.alias or param_name

    if not param_annotation == inspect.Parameter.empty:
        annotation = param_annotation

    field = create_model_field(
        name=param_name,
        type_=get_annotation_from_field_info(annotation, field_info, param_name),
        default=None if required else default_value,
        alias=alias,
        required=required,
        field_info=field_info,
    )
    field.required = required

    if not had_schema and not is_scalar_field(field=field):
        field.field_info = body_field_class(field_info.default)

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
        param_converters: t.Dict[str, Convertor],
        extra_endpoint_args: t.Sequence[ExtraEndpointArg] = None,
    ) -> None:
        self.path = path
        self.param_converters = param_converters
        self._computation_models: t.DefaultDict[
            str, t.List[BaseRouteParameterResolver]
        ] = defaultdict(list)
        self.path_param_names = self.get_path_param_names(path)
        self.endpoint_signature = self.get_typed_signature(endpoint)
        self.body_resolver: t.Optional[t.Union[t.Any, RouteParameterResolver]] = None
        self._route_models: t.List[BaseRouteParameterResolver] = []
        self._extra_endpoint_args: t.List[ExtraEndpointArg] = (
            list(extra_endpoint_args) if extra_endpoint_args else []
        )

    def get_route_models(self) -> t.List[BaseRouteParameterResolver]:
        """
        Returns all computed endpoint resolvers required for function execution
        :return: List[BaseRouteParameterResolver]
        """
        return self._route_models

    def get_all_models(self) -> t.List[BaseRouteParameterResolver]:
        """
        Returns all computed endpoint resolvers + omitted resolvers
        :return: List[BaseRouteParameterResolver]
        """
        return (
            self.get_route_models() + self._computation_models[ROUTE_OPENAPI_PARAMETERS]
        )

    def get_omitted_prefix(self) -> None:
        """
        Tracks for omitted path parameters for OPENAPI purpose
        :return: None
        """
        _omitted = []
        signature_dict = dict(self.endpoint_signature.parameters)
        for name, _converter in self.param_converters.items():
            if name in signature_dict:
                continue

            _converter_signature = inspect.signature(_converter.convert)
            assert (
                _converter_signature.return_annotation is not inspect.Parameter.empty
            ), "Convertor must have return type"
            _type = _converter_signature.return_annotation
            _omitted.append(
                ExtraEndpointArg(
                    name=name, annotation=_type, default_value=params.Path()
                )
            )

        self._add_extra_route_args(*_omitted, key=ROUTE_OPENAPI_PARAMETERS)

    def build_model(self) -> None:
        """
        Run all endpoint model resolver computation
        :return:
        """
        self._computation_models = defaultdict(list)
        self.get_omitted_prefix()
        self.compute_route_parameter_list()
        self.compute_extra_route_args()
        self.build_body_field()
        self._route_models = (
            self._computation_models[params.Header.in_.value]
            + self._computation_models[params.Path.in_.value]
            + self._computation_models[params.Query.in_.value]
            + self._computation_models[params.Cookie.in_.value]
            + self._computation_models[NonFieldRouteParameterResolver.in_]
        )

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
            if (
                param_name in ("request", "req")
                and param.default == inspect.Parameter.empty
            ):
                request_inject = ParameterInjectable()(param_name, Request)
                self._computation_models[request_inject.in_].append(request_inject)
                continue

            if (
                param_name == ("websocket", "ws")
                and param.default == inspect.Parameter.empty
            ):
                websocket_inject = ParameterInjectable()(param_name, WebSocket)
                self._computation_models[websocket_inject.in_].append(websocket_inject)
                continue

            if (
                param_name == ("context", "ctx")
                and param.default == inspect.Parameter.empty
            ):
                context_inject = ParameterInjectable()(
                    param_name, t.cast(t.Type, IExecutionContext)
                )
                self._computation_models[context_inject.in_].append(context_inject)
                continue

            if self._add_non_field_param_to_dependency(
                param_name=param.name,
                param_default=param.default,
                param_annotation=param.annotation,
            ):
                continue

            if param_name in self.path_param_names:
                if isinstance(param.default, params.Path):
                    ignore_default = False
                else:
                    ignore_default = True
                param_field = get_parameter_field(
                    param_default=param.default,
                    param_annotation=param.annotation,
                    param_name=param_name,
                    default_field_info=params.Path,
                    ignore_default=ignore_default,
                )
                assert is_scalar_field(
                    field=param_field
                ), "Path params must be of one of the supported types"
                self._add_to_model(field=param_field)
            else:
                default_field_info = t.cast(
                    t.Type[params.Param],
                    param.default
                    if isinstance(param.default, FieldInfo)
                    else params.Query,
                )
                param_field = get_parameter_field(
                    param_default=param.default,
                    param_annotation=param.annotation,
                    default_field_info=default_field_info,
                    param_name=param_name,
                    body_field_class=body_field_class,
                )
                if isinstance(
                    param.default, (params.Query, params.Header, params.Cookie)
                ) and not is_scalar_field(field=param_field):
                    if not is_scalar_sequence_field(param_field):
                        if not lenient_issubclass(param_field.outer_type_, BaseModel):
                            raise ImproperConfiguration(
                                f"{param_field.outer_type_} type can't be processed as a field"
                            )

                        pydantic_type = t.cast(BaseModel, param_field.outer_type_)
                        resolvers = []
                        for k, field in pydantic_type.__fields__.items():
                            if not is_scalar_field(
                                field=field
                            ) and not is_scalar_sequence_field(param_field):
                                raise ImproperConfiguration(
                                    f"field: '{k}' with annotation:'{field.type_}' "
                                    f"can't be processed. Field type should belong to {sequence_types} "
                                    f"or any primitive type"
                                )
                            convert_underscores = getattr(
                                param_field.field_info,
                                "convert_underscores",
                                getattr(
                                    param_field.field_info.extra,
                                    "convert_underscores",
                                    None,
                                ),
                            )

                            field_info_type: t.Type[params.Param] = t.cast(
                                t.Type[params.Param], type(param_field.field_info)
                            )

                            keys = dict(
                                default=None,
                                default_factory=None,
                                alias=None,
                                alias_priority=None,
                                title=None,
                                description=None,
                                **field.field_info.__class__.__field_constraints__,
                                **{"convert_underscores": convert_underscores}
                                if convert_underscores
                                else dict(),
                            )

                            attrs = {
                                k: getattr(field.field_info, k, v)
                                for k, v in keys.items()
                            }

                            field_info = field_info_type(**attrs)  # type:ignore

                            model_field = get_parameter_field(
                                param_default=field_info,
                                param_annotation=field.type_,
                                default_field_info=field_info_type,
                                param_name=field_info.alias or k,
                                body_field_class=body_field_class,
                            )
                            resolver = field_info.create_resolver(
                                model_field=model_field
                            )
                            resolvers.append(resolver)

                        param_field.field_info.extra[MULTI_RESOLVER_KEY] = resolvers
                self._add_to_model(field=param_field)

    def _add_non_field_param_to_dependency(
        self,
        *,
        param_default: t.Any,
        param_name: str,
        param_annotation: t.Optional[t.Type],
        key: str = None,
    ) -> t.Optional[bool]:
        if isinstance(param_default, NonFieldRouteParameterResolver):
            model = param_default(param_name, param_annotation)  # type:ignore
            self._computation_models[key or model.in_].append(model)
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

    def _add_to_model(self, *, field: ModelField, key: str = None) -> None:
        field_info = t.cast(params.Param, field.field_info)
        self._computation_models[str(key or field_info.in_.value)].append(
            field_info.create_resolver(model_field=field)
        )

    async def resolve_dependencies(
        self, *, ctx: IExecutionContext
    ) -> t.Tuple[t.Dict[str, t.Any], t.List[ErrorWrapper]]:
        values: t.Dict[str, t.Any] = {}
        errors: t.List[ErrorWrapper] = []

        if self.body_resolver:
            await self.resolve_body(ctx, values, errors)

        if not errors:
            for parameter_resolver in self._route_models:
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

    def compute_extra_route_args(self) -> None:
        self._add_extra_route_args(*self._extra_endpoint_args)

    def _add_extra_route_args(
        self, *extra_operation_args: ExtraEndpointArg, key: str = None
    ) -> None:
        for param in extra_operation_args:
            if self._add_non_field_param_to_dependency(
                param_name=param.name,
                param_default=param.default,
                param_annotation=param.annotation,
                key=key,
            ):
                continue

            default_field_info = t.cast(
                t.Type[params.Param],
                param.default if isinstance(param.default, FieldInfo) else params.Query,
            )
            param_field = get_parameter_field(
                param_default=param.default,
                param_annotation=param.annotation,
                default_field_info=default_field_info,
                param_name=param.name,
            )
            self._add_to_model(field=param_field, key=key)

    async def resolve_body(
        self, ctx: IExecutionContext, values: t.Dict, errors: t.List
    ) -> None:
        """Body Resolver Implementation"""

    def __deepcopy__(
        self, memodict: t.Dict = {}
    ) -> "EndpointArgsModel":  # pragma: no cover
        return self.__copy__(memodict)

    def __copy__(
        self, memodict: t.Dict = {}
    ) -> "EndpointArgsModel":  # pragma: no cover
        return self

    def build_body_field(self) -> None:
        raise NotImplementedError


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
        self.body_resolver = None

        body_resolvers = self._computation_models[params.Body.in_.value]
        if body_resolvers and len(body_resolvers) == 1:
            self.body_resolver = body_resolvers[0]
        elif body_resolvers:
            # if body_resolvers is more than one, we create a bulk_body_resolver instead
            _body_resolvers_model_fields = (
                t.cast(RouteParameterResolver, item).model_field
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


class WebsocketEndpointArgsModel(EndpointArgsModel):
    body_resolver: t.List[RouteParameterResolver]

    def __init__(
        self,
        *,
        path: str,
        endpoint: t.Callable,
        param_converters: t.Dict[str, Convertor],
        extra_endpoint_args: t.Sequence[ExtraEndpointArg] = None,
    ) -> None:
        super().__init__(
            path=path,
            endpoint=endpoint,
            param_converters=param_converters,
            extra_endpoint_args=extra_endpoint_args,
        )

    def build_body_field(self) -> None:
        for resolver in list(self._computation_models):
            if isinstance(resolver, WsBodyParameterResolver):
                self.body_resolver.append(resolver)
                self._computation_models[
                    resolver.model_field.field_info.in_.value
                ].remove(resolver)

        if self.body_resolver and len(self.body_resolver) > 1:
            for resolver in self.body_resolver:  # type:ignore
                setattr(resolver.model_field.field_info, "embed", True)  # type:ignore

    def compute_route_parameter_list(
        self, body_field_class: t.Type[FieldInfo] = params.Body
    ) -> None:
        super().compute_route_parameter_list(body_field_class=params.WsBody)

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
