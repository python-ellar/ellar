import typing as t
from abc import ABC, abstractmethod

from ellar.common.compatible import AttributeDict, cached_property
from ellar.common.constants import (
    GUARDS_KEY,
    METHODS_WITH_BODY,
    REF_PREFIX,
)
from ellar.common.params.args import EndpointArgsModel
from ellar.common.params.params import BodyFieldInfo as Body
from ellar.common.params.params import ParamFieldInfo as Param
from ellar.common.params.resolvers import (
    BaseRouteParameterResolver,
    BodyParameterResolver,
    BulkParameterResolver,
    RouteParameterModelField,
)
from ellar.common.shortcuts import normalize_path
from ellar.core.routing import EllarControllerMount, RouteOperation
from ellar.core.services.reflector import reflector
from ellar.openapi.constants import (
    IGNORE_CONTROLLER_TYPE,
    OPENAPI_OPERATION_KEY,
    OPENAPI_TAG,
)
from ellar.pydantic import (
    JsonSchemaValue,
    ModelField,
    get_schema_from_model_field,
)
from starlette.routing import Mount, compile_path
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common import GuardCanActivate


class OpenAPIRoute(ABC):
    @abstractmethod
    def get_route_models(self) -> t.List[t.Union[ModelField, RouteParameterModelField]]:
        pass

    @abstractmethod
    def get_openapi_path(
        self,
        paths: t.Dict,
        security_schemes: t.Dict[str, t.Any],
        field_mapping: t.Dict[
            t.Tuple[ModelField, t.Literal["validation", "serialization"]],
            JsonSchemaValue,
        ],
        path_prefix: t.Optional[str] = None,
    ) -> None:
        pass


class OpenAPIMountDocumentation(OpenAPIRoute):
    def __init__(
        self,
        mount: t.Union[EllarControllerMount, Mount],
        global_route_models_update: t.Callable[
            ["OpenAPIMountDocumentation", t.Dict], t.Any
        ],
        name: t.Optional[str] = None,
        global_guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = None,
        path_prefix: t.Optional[str] = None,
    ) -> None:
        self.tag = name
        self.mount = mount
        self.path_regex, self.path_format, self.param_convertors = compile_path(
            normalize_path(f"/{path_prefix}/{mount.path}")
            if path_prefix
            else mount.path
        )
        # if there is some convertor on ModuleMount Object, then we need to convert it to ModelField
        self.global_route_parameters: t.List[ModelField] = [
            EndpointArgsModel.get_convertor_model_field(name, convertor)
            for name, convertor in self.param_convertors.items()
        ]
        self.global_guards = global_guards or []
        self._global_route_models_update = global_route_models_update
        self.routes: t.List["OpenAPIRouteDocumentation"] = self._build_routes()

    def _build_routes(self) -> t.List["OpenAPIRouteDocumentation"]:
        routes: t.List[OpenAPIRouteDocumentation] = []

        for route in self.mount.routes:
            if isinstance(route, RouteOperation) and route.include_in_schema:
                openapi = reflector.get(OPENAPI_OPERATION_KEY, route.endpoint) or {}
                guards = reflector.get(GUARDS_KEY, route.endpoint)

                if not openapi.get("tags", False):
                    openapi.update(tags=[self.tag] if self.tag else ["default"])

                routes.append(
                    OpenAPIRouteDocumentation(
                        route=route,
                        global_route_parameters=self.global_route_parameters,
                        guards=guards or self.global_guards,
                        **openapi,
                    )
                )
            elif isinstance(route, EllarControllerMount):
                openapi_tags = AttributeDict(reflector.get(OPENAPI_TAG, route) or {})
                ignore_tag = reflector.get(IGNORE_CONTROLLER_TYPE, route) or False
                if route.name:
                    openapi_tags.setdefault("name", route.name)

                openapi_tags.update(name=f"{self.tag}:{openapi_tags.name}")

                guards = reflector.get(GUARDS_KEY, route)

                self._global_route_models_update(
                    OpenAPIMountDocumentation(
                        mount=route,
                        global_guards=guards or self.global_guards,
                        name=openapi_tags.name,
                        global_route_models_update=self._global_route_models_update,
                        path_prefix=self.path_format,
                    ),
                    openapi_tags if not ignore_tag else None,
                )
        return routes

    @cached_property
    def _openapi_models(self) -> t.List[ModelField]:
        _models = []
        for route in self.routes:
            _models.extend(route.get_route_models())
        return _models

    def get_route_models(self) -> t.List[t.Union[ModelField, RouteParameterModelField]]:
        """Should return input fields and output fields"""
        return self._openapi_models

    def get_openapi_path(
        self,
        paths: t.Dict,
        security_schemes: t.Dict[str, t.Any],
        field_mapping: t.Dict[
            t.Tuple[ModelField, t.Literal["validation", "serialization"]],
            JsonSchemaValue,
        ],
        path_prefix: t.Optional[str] = None,
    ) -> None:
        path_prefix = (
            f"{path_prefix.rstrip('/')}/{self.mount.path.lstrip('/')}"
            if path_prefix
            else self.path_format
        )
        for openapi_route in self.routes:
            openapi_route.get_openapi_path(
                paths=paths,
                security_schemes=security_schemes,
                field_mapping=field_mapping,
                path_prefix=path_prefix,
            )


class OpenAPIRouteDocumentation(OpenAPIRoute):
    def __init__(
        self,
        *,
        route: "RouteOperation",
        operation_id: t.Optional[str] = None,
        summary: t.Optional[str] = None,
        description: t.Optional[str] = None,
        tags: t.Optional[t.List[str]] = None,
        deprecated: t.Optional[bool] = None,
        global_route_parameters: t.Optional[t.List[ModelField]] = None,
        guards: t.Optional[
            t.List[t.Union["GuardCanActivate", t.Type["GuardCanActivate"]]]
        ] = None,
        **operation_extra: t.Any,
    ) -> None:
        self.operation_id = operation_id
        self.summary = summary
        self.description = description
        self.tags = tags
        self.deprecated = deprecated
        self.route = route
        self.global_route_parameters = (
            list(global_route_parameters) if global_route_parameters else []
        )
        self.guards = guards or []
        self._operation_extra = operation_extra

    @cached_property
    def _openapi_models(self) -> t.List[t.Union[ModelField, RouteParameterModelField]]:
        _models: t.List[ModelField] = self.input_fields + self.output_fields
        if self.route.endpoint_parameter_model.body_resolver:
            model_field = self.route.endpoint_parameter_model.body_resolver.model_field
            _models.append(model_field)
        return _models

    @cached_property
    def input_fields(self) -> t.List[ModelField]:
        omitted_path_parameter_fields = (
            self.route.endpoint_parameter_model.get_omitted_prefix()
        )
        _models: t.List[ModelField] = self.global_route_parameters

        for item in self.route.endpoint_parameter_model.get_all_models():
            if isinstance(item, BodyParameterResolver):  # pragma: no cover
                # just incase we have a Body Field
                continue

            if isinstance(item, BulkParameterResolver):
                _models.extend(item.get_model_fields())
                continue

            if isinstance(item, BaseRouteParameterResolver):
                _models.append(item.model_field)

        already_existing_parameter_names = [model.name for model in _models]
        for omitted_path_parameter_field in omitted_path_parameter_fields:
            if omitted_path_parameter_field.name in already_existing_parameter_names:
                continue
            _models.append(omitted_path_parameter_field)

        return _models

    @cached_property
    def output_fields(self) -> t.List[ModelField]:
        _models: t.List[ModelField] = []
        for _, model in self.route.response_model.models.items():
            if model.get_model_field():
                _models.append(model.get_model_field())  # type: ignore
        return _models

    def get_route_models(self) -> t.List[ModelField]:
        """Should return input fields and output fields"""
        return self._openapi_models

    def _get_openapi_security_scheme(
        self,
    ) -> t.Tuple[t.Dict[str, t.Any], t.List[t.Dict[str, t.Any]]]:
        security_definitions: t.Dict = {}
        operation_security: t.List = []
        for item in self.guards:
            if not hasattr(item, "openapi_security_scheme"):
                continue
            security_scheme = item.openapi_security_scheme(self.route)
            security_definitions.update(security_scheme)

            keys = list(security_scheme.keys())
            if keys:
                scheme_name = keys[0]
                operation_security.append(
                    {scheme_name: item.openapi_scope}  # type:ignore[union-attr]
                )

        return security_definitions, operation_security

    def get_openapi_operation_metadata(self, method: str) -> t.Dict[str, t.Any]:
        operation: t.Dict[str, t.Any] = {}
        if self.tags:
            operation["tags"] = self.tags

        operation["summary"] = self.summary

        if self.description:
            operation["description"] = self.description

        ignore_controller = (
            reflector.get(IGNORE_CONTROLLER_TYPE, self.route.endpoint) or False
        )

        operation["operationId"] = (
            self.operation_id
            or self.route.get_operation_unique_id(
                methods=method,
                controller=None if ignore_controller else self.route.router_reflect_key,
            )
        )
        if self.deprecated:
            operation["deprecated"] = self.deprecated

        return operation

    def get_openapi_operation_parameters(
        self,
        *,
        field_mapping: t.Dict[
            t.Tuple[ModelField, t.Literal["validation", "serialization"]],
            JsonSchemaValue,
        ],
    ) -> t.List[t.Dict[str, t.Any]]:
        parameters: t.List[t.Dict[str, t.Any]] = []
        for param in self.input_fields:
            field_info = param.field_info
            field_info = t.cast(Param, field_info)
            param_schema = get_schema_from_model_field(
                field=param,
                field_mapping=field_mapping,
                separate_input_output_schemas=True,
            )
            parameter = {
                "name": param.alias,
                "in": field_info.in_.value,
                "required": param.required,
                "schema": param_schema,
            }
            if field_info.description:
                parameter["description"] = field_info.description
            if field_info.examples:  # pragma: no cover
                parameter["examples"] = field_info.examples  # type:ignore[assignment]
            if field_info.deprecated:
                parameter["deprecated"] = field_info.deprecated  # type:ignore[assignment]
            parameters.append(parameter)
        return parameters

    def get_openapi_operation_request_body(
        self,
        *,
        field_mapping: t.Dict[
            t.Tuple[ModelField, t.Literal["validation", "serialization"]],
            JsonSchemaValue,
        ],
    ) -> t.Optional[t.Dict[str, t.Any]]:
        if not self.route.endpoint_parameter_model.body_resolver:
            return None

        model_field = self.route.endpoint_parameter_model.body_resolver.model_field
        assert isinstance(model_field, ModelField)

        body_schema = get_schema_from_model_field(
            field=model_field,
            field_mapping=field_mapping,
            separate_input_output_schemas=True,
        )

        field_info = t.cast(Body, model_field.field_info)
        request_media_type = field_info.media_type

        request_body_oai: t.Dict[str, t.Any] = {}
        if model_field.required:
            request_body_oai["required"] = model_field.required

        request_media_content: t.Dict[str, t.Any] = {"schema": body_schema}
        if field_info.examples:  # pragma: no cover
            request_media_content["examples"] = field_info.examples

        request_body_oai["content"] = {request_media_type: request_media_content}
        return request_body_oai

    def _get_openapi_path_object(
        self,
        field_mapping: t.Dict[
            t.Tuple[ModelField, t.Literal["validation", "serialization"]],
            JsonSchemaValue,
        ],
    ) -> t.Tuple:
        path: t.Dict = {}
        security_schemes: t.Dict[str, t.Any] = {}

        for method in self.route.methods:
            operation = self.get_openapi_operation_metadata(method=method)
            parameters: t.List[t.Dict[str, t.Any]] = []
            operation_parameters = self.get_openapi_operation_parameters(
                field_mapping=field_mapping,
            )
            parameters.extend(operation_parameters)

            if parameters:
                operation["parameters"] = list(
                    {param["name"]: param for param in parameters}.values()
                )

            if method in METHODS_WITH_BODY:
                request_body_oai = self.get_openapi_operation_request_body(
                    field_mapping=field_mapping,
                )
                if request_body_oai:
                    operation["requestBody"] = request_body_oai

            (
                security_definitions,
                operation_security,
            ) = self._get_openapi_security_scheme()
            if operation_security:
                operation.setdefault("security", []).extend(operation_security)
            if security_definitions:
                security_schemes.update(security_definitions)

            operation_responses = operation.setdefault("responses", {})
            for status, response_model in self.route.response_model.models.items():
                operation_responses_status = operation_responses.setdefault(
                    str(status), {}
                )
                operation_responses_status["description"] = response_model.description

                content = operation_responses_status.setdefault("content", {})
                media_type = content.setdefault(response_model.media_type, {})
                media_type.setdefault("schema", {"type": "string"})

                model_field = response_model.get_model_field()
                if model_field:
                    model_field_schema = get_schema_from_model_field(
                        field=model_field,
                        field_mapping=field_mapping,
                        separate_input_output_schemas=True,
                    )
                    media_type["schema"] = model_field_schema

            http422 = str(HTTP_422_UNPROCESSABLE_ENTITY)
            if (
                parameters or self.route.endpoint_parameter_model.body_resolver
            ) and not any(
                status in operation["responses"]
                for status in [http422, "4XX", "default"]
            ):
                operation["responses"][http422] = {
                    "description": "Validation Error",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": REF_PREFIX + "HTTPValidationError"}
                        }
                    },
                }
            if self._operation_extra:
                operation.update(self._operation_extra)
            path[method.lower()] = operation

        return path, security_schemes

    def get_child_openapi_path(
        self,
        field_mapping: t.Dict[
            t.Tuple[ModelField, t.Literal["validation", "serialization"]],
            JsonSchemaValue,
        ],
    ) -> t.Tuple:
        _path, _security_schemes = self._get_openapi_path_object(
            field_mapping=field_mapping,
        )
        return _path, _security_schemes

    def get_openapi_path(
        self,
        paths: t.Dict,
        security_schemes: t.Dict[str, t.Any],
        field_mapping: t.Dict[
            t.Tuple[ModelField, t.Literal["validation", "serialization"]],
            JsonSchemaValue,
        ],
        path_prefix: t.Optional[str] = None,
    ) -> None:
        path, _security_schemes = self.get_child_openapi_path(
            field_mapping=field_mapping,
        )
        if path:
            route_path = (
                normalize_path(f"{path_prefix}/{self.route.path_format}")
                if path_prefix
                else self.route.path_format
            )
            paths.setdefault(route_path, {}).update(path)
        security_schemes.update(_security_schemes)
