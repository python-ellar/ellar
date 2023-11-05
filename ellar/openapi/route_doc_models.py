import typing as t
from abc import ABC, abstractmethod
from enum import Enum

from ellar.common.compatible import cached_property
from ellar.common.constants import GUARDS_KEY, METHODS_WITH_BODY, REF_PREFIX
from ellar.common.params.args import EndpointArgsModel
from ellar.common.params.params import BodyFieldInfo as Body
from ellar.common.params.params import ParamFieldInfo as Param
from ellar.common.params.resolvers import (
    BaseRouteParameterResolver,
    BodyParameterResolver,
    BulkParameterResolver,
    RouteParameterModelField,
)
from ellar.common.routing import ModuleMount, RouteOperation
from ellar.common.shortcuts import normalize_path
from ellar.core.services.reflector import Reflector
from ellar.openapi.constants import OPENAPI_OPERATION_KEY
from pydantic import BaseModel
from pydantic.fields import ModelField, Undefined
from pydantic.schema import field_schema
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
        model_name_map: t.Dict[t.Union[t.Type[BaseModel], t.Type[Enum]], str],
        paths: t.Dict,
        security_schemes: t.Dict[str, t.Any],
        path_prefix: t.Optional[str] = None,
    ) -> None:
        pass


class OpenAPIMountDocumentation(OpenAPIRoute):
    def __init__(
        self,
        mount: t.Union[ModuleMount, Mount],
        name: t.Optional[str] = None,
        global_guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = None,
    ) -> None:
        self.tag = name
        self.mount = mount
        self.path_regex, self.path_format, self.param_convertors = compile_path(
            self.mount.path
        )
        # if there is some convertor on ModuleMount Object, then we need to convert it to ModelField
        self.global_route_parameters: t.List[ModelField] = [
            EndpointArgsModel.get_convertor_model_field(name, convertor)
            for name, convertor in self.param_convertors.items()
        ]
        self.global_guards = global_guards or []

        self._routes: t.List["OpenAPIRouteDocumentation"] = self._build_routes()

    def _build_routes(self) -> t.List["OpenAPIRouteDocumentation"]:
        reflector: Reflector = Reflector()
        _routes: t.List[OpenAPIRouteDocumentation] = []

        for route in self.mount.routes:
            if isinstance(route, RouteOperation) and route.include_in_schema:
                openapi = reflector.get(OPENAPI_OPERATION_KEY, route.endpoint) or {}
                guards = reflector.get(GUARDS_KEY, route.endpoint)
                openapi.setdefault("tags", [self.tag] if self.tag else ["default"])
                _routes.append(
                    OpenAPIRouteDocumentation(
                        route=route,
                        global_route_parameters=self.global_route_parameters,
                        guards=guards or self.global_guards,
                        **openapi,
                    )
                )
        return _routes

    @cached_property
    def _openapi_models(self) -> t.List[ModelField]:
        _models = []
        for route in self._routes:
            _models.extend(route.get_route_models())
        return _models

    def get_route_models(self) -> t.List[t.Union[ModelField, RouteParameterModelField]]:
        """Should return input fields and output fields"""
        return self._openapi_models

    def get_openapi_path(
        self,
        model_name_map: t.Dict[t.Union[t.Type[BaseModel], t.Type[Enum]], str],
        paths: t.Dict,
        security_schemes: t.Dict[str, t.Any],
        path_prefix: t.Optional[str] = None,
    ) -> None:
        path_prefix = (
            f"{path_prefix.rstrip('/')}/{self.mount.path.lstrip('/')}"
            if path_prefix
            else self.path_format
        )
        for openapi_route in self._routes:
            openapi_route.get_openapi_path(
                model_name_map=model_name_map,
                paths=paths,
                security_schemes=security_schemes,
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

        if self.tags and not isinstance(self.tags, list):
            self.tags = [self.tags]

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
            if isinstance(item, BodyParameterResolver):
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

        operation[
            "operationId"
        ] = self.operation_id or self.route.get_operation_unique_id(methods=method)
        if self.deprecated:
            operation["deprecated"] = self.deprecated

        return operation

    def get_openapi_operation_parameters(
        self,
        *,
        model_name_map: t.Dict[t.Union[t.Type[BaseModel], t.Type[Enum]], str],
    ) -> t.List[t.Dict[str, t.Any]]:
        parameters: t.List[t.Dict[str, t.Any]] = []
        for param in self.input_fields:
            field_info = param.field_info
            field_info = t.cast(Param, field_info)
            parameter = {
                "name": param.alias,
                "in": field_info.in_.value,
                "required": param.required,
                "schema": field_schema(
                    param, model_name_map=model_name_map, ref_prefix=REF_PREFIX
                )[0],
            }
            if field_info.description:
                parameter["description"] = field_info.description
            if field_info.examples:
                parameter["examples"] = field_info.examples
            elif field_info.example != Undefined:
                parameter["example"] = field_info.example
            if field_info.deprecated:
                parameter["deprecated"] = field_info.deprecated
            parameters.append(parameter)
        return parameters

    def get_openapi_operation_request_body(
        self,
        *,
        model_name_map: t.Dict[t.Union[t.Type[BaseModel], t.Type[Enum]], str],
    ) -> t.Optional[t.Dict[str, t.Any]]:
        if not self.route.endpoint_parameter_model.body_resolver:
            return None
        model_field = self.route.endpoint_parameter_model.body_resolver.model_field
        assert isinstance(model_field, ModelField)
        body_schema, _, _ = field_schema(
            model_field, model_name_map=model_name_map, ref_prefix=REF_PREFIX
        )
        field_info = t.cast(Body, model_field.field_info)
        request_media_type = field_info.media_type
        request_body_oai: t.Dict[str, t.Any] = {}
        if model_field.required:
            request_body_oai["required"] = model_field.required
        request_media_content: t.Dict[str, t.Any] = {"schema": body_schema}
        if field_info.examples:
            request_media_content["examples"] = field_info.examples
        elif field_info.example != Undefined:
            request_media_content["example"] = field_info.example
        request_body_oai["content"] = {request_media_type: request_media_content}
        return request_body_oai

    def _get_openapi_path_object(
        self, model_name_map: t.Dict[t.Union[t.Type[BaseModel], t.Type[Enum]], str]
    ) -> t.Tuple:
        path: t.Dict = {}
        security_schemes: t.Dict[str, t.Any] = {}

        for method in self.route.methods:
            operation = self.get_openapi_operation_metadata(method=method)
            parameters: t.List[t.Dict[str, t.Any]] = []
            operation_parameters = self.get_openapi_operation_parameters(
                model_name_map=model_name_map
            )
            parameters.extend(operation_parameters)
            if parameters:
                operation["parameters"] = list(
                    {param["name"]: param for param in parameters}.values()
                )
            if method in METHODS_WITH_BODY:
                request_body_oai = self.get_openapi_operation_request_body(
                    model_name_map=model_name_map
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
                operation_responses_status = operation_responses.setdefault(status, {})
                operation_responses_status["description"] = response_model.description

                content = operation_responses_status.setdefault("content", {})
                media_type = content.setdefault(response_model.media_type, {})
                media_type.setdefault("schema", {"type": "string"})

                model_field = response_model.get_model_field()
                if model_field:
                    model_field_schema, _, _ = field_schema(
                        model_field,
                        model_name_map=model_name_map,
                        ref_prefix=REF_PREFIX,
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
            path[method.lower()] = operation

        return path, security_schemes

    def get_child_openapi_path(
        self,
        model_name_map: t.Dict[t.Union[t.Type[BaseModel], t.Type[Enum]], str],
    ) -> t.Tuple:
        _path, _security_schemes = self._get_openapi_path_object(
            model_name_map=model_name_map
        )
        return _path, _security_schemes

    def get_openapi_path(
        self,
        model_name_map: t.Dict[t.Union[t.Type[BaseModel], t.Type[Enum]], str],
        paths: t.Dict,
        security_schemes: t.Dict[str, t.Any],
        path_prefix: t.Optional[str] = None,
    ) -> None:
        path, _security_schemes = self.get_child_openapi_path(
            model_name_map=model_name_map
        )
        if path:
            route_path = (
                normalize_path(f"{path_prefix}/{self.route.path_format}")
                if path_prefix
                else self.route.path_format
            )
            paths.setdefault(route_path, {}).update(path)
        security_schemes.update(_security_schemes)
