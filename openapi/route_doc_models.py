import typing as t
from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel
from pydantic.fields import ModelField, Undefined
from pydantic.schema import field_schema
from starlette.routing import Mount
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from starletteapi.constants import METHODS_WITH_BODY, REF_PREFIX
from starletteapi.guard import GuardCanActivate, BaseAuthGuard
from starletteapi.helper import cached_property
from starletteapi.route_models.param_resolvers import RouteParameterResolver, BodyParameterResolver
from starletteapi.route_models.params import Param, Body
from starletteapi.routing.operations import Operation
from starletteapi.shortcuts import normalize_path

if t.TYPE_CHECKING:
    from starletteapi.main import StarletteApp


class OpenAPIRoute(ABC):
    @abstractmethod
    def get_route_models(self) -> t.List[ModelField]:
        pass

    @abstractmethod
    def get_openapi_path(
            self, model_name_map: t.Dict[t.Union[t.Type[BaseModel], t.Type[Enum]], str],
            path_prefix: t.Optional[str] = None
    ):
        pass


class OpenAPIMountDocumentation(OpenAPIRoute):
    def __init__(
            self,
            mount: Mount,
            tag: t.Optional[str] = None,
            description: t.Optional[str] = None,
            external_doc_description: t.Optional[str] = None,
            external_doc_url: t.Optional[str] = None,
    ):
        meta: t.Dict = dict()
        if hasattr(mount, 'get_meta') and callable(mount.get_meta):
            meta = mount.get_meta()
        self.tag = tag or meta.get('tag')
        self.description = description or meta.get('description')
        self.external_doc_description = external_doc_description or meta.get('external_doc_description')
        self.external_doc_url = external_doc_url or meta.get('external_doc_url')
        self.mount = mount

    def get_tag(self):
        if self.tag:
            return dict(
                name=self.tag, description=self.description,
                externalDocs=dict(description=self.external_doc_description, url=self.external_doc_url)
            )
        return dict()

    @cached_property
    def routes(self) -> t.List['OpenAPIRouteDocumentation']:
        _routes: t.List['OpenAPIRouteDocumentation'] = []
        for route in self.mount.routes:
            if isinstance(route, Operation):
                _routes.append(
                    OpenAPIRouteDocumentation(route=route, global_tag=self.tag)
                )
        return _routes

    @cached_property
    def _openapi_models(self):
        _models = []
        for route in self.routes:
            _models.extend(route.get_route_models())
        return _models

    def get_route_models(self):
        """Should return input fields and output fields"""
        return self._openapi_models

    def get_openapi_path(
            self, model_name_map: t.Dict[t.Union[t.Type[BaseModel], t.Type[Enum]], str],
            path_prefix: t.Optional[str] = None
    ):
        path_prefix = f"{path_prefix.rstrip('/')}/{self.mount.path.lstrip('/')}" if path_prefix else self.mount.path
        paths = {}
        security_schemes: t.Dict[str, t.Any] = {}
        for route in self.routes:
            path, _security_schemes = route.get_openapi_path(
                model_name_map=model_name_map, path_prefix=path_prefix
            )
            paths.update(**path)
            security_schemes.update(_security_schemes)
        return paths, security_schemes


class OpenAPIRouteDocumentation(OpenAPIRoute):
    def __init__(
            self,
            *,
            route: 'Operation',
            operation_id: t.Optional[str] = None,
            summary: t.Optional[str] = None,
            description: t.Optional[str] = None,
            tags: t.Optional[t.List[str]] = None,
            deprecated: t.Optional[bool] = None,
            global_tag: t.Optional[str] = None
    ):

        self.operation_id = operation_id or route.get_meta().get('operation_id')
        self.summary = summary or route.get_meta().get('summary')
        self.description = description or route.get_meta().get('description')
        self.tags = tags or route.get_meta().get('tags') or global_tag
        self.deprecated = deprecated or route.get_meta().get('deprecated')
        self.route = route

        if self.tags and not isinstance(self.tags, list):
            self.tags = [self.tags]

    @cached_property
    def _openapi_models(self):
        _models = self.input_fields + self.output_fields
        if self.route.route_parameter_model.body_resolver:
            model_field = self.route.route_parameter_model.body_resolver.model_field
            _models.append(model_field)
        return _models

    @cached_property
    def input_fields(self) -> t.List[ModelField]:
        _models = []
        for item in self.route.route_parameter_model.get_models():
            if isinstance(item, BodyParameterResolver):
                continue
            if isinstance(item, RouteParameterResolver):
                _models.append(item.model_field)
        return _models

    @cached_property
    def output_fields(self) -> t.List[ModelField]:
        _models = []
        for _, model in self.route.response_model.models.items():
            if model.get_model_field():
                _models.append(model.get_model_field())
        return _models

    def get_route_models(self):
        """Should return input fields and output fields"""
        return self._openapi_models

    def _get_openapi_security_scheme(self) -> t.Tuple[t.Dict[str, t.Any], t.List[t.Dict[str, t.Any]]]:
        security_definitions = {}
        operation_security = []
        for item in self.route.get_guards():
            if (isinstance(item, type) and not issubclass(item, BaseAuthGuard)):
                continue
            security_scheme = item.get_guard_scheme()
            scheme_name = security_scheme['name']
            operation_security.append({scheme_name: item.openapi_scope})
            security_definitions[scheme_name] = security_scheme
        return security_definitions, operation_security

    def get_openapi_operation_metadata(self, method: str):
        operation: t.Dict[str, t.Any] = {}
        if self.tags:
            operation["tags"] = self.tags

        operation["summary"] = self.summary

        if self.description:
            operation["description"] = self.description

        operation["operationId"] = self.operation_id or self.route.get_operation_unique_id(method=method)
        if self.deprecated:
            operation["deprecated"] = self.deprecated

        return operation

    def get_openapi_operation_parameters(
            self,
            *,
            model_name_map: t.Dict[t.Union[t.Type[BaseModel], t.Type[Enum]], str],
    ) -> t.List[t.Dict[str, t.Any]]:
        parameters = []
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
        if not self.route.route_parameter_model.body_resolver:
            return None
        model_field = self.route.route_parameter_model.body_resolver.model_field
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
    ):
        path = {}
        security_schemes: t.Dict[str, t.Any] = {}

        if self.route.include_in_schema:
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

                security_definitions, operation_security = self._get_openapi_security_scheme()
                if operation_security:
                    operation.setdefault("security", []).extend(operation_security)
                if security_definitions:
                    security_schemes.update(security_definitions)

                operation_responses = operation.setdefault("responses", {})
                for status, response_model in self.route.response_model.models.items():
                    operation_responses_status = operation_responses.setdefault(status, {})
                    operation_responses_status['description'] = getattr(response_model, 'description', '')

                    content = operation_responses_status.setdefault("content", {})
                    media_type = content.setdefault(getattr(response_model, 'media_type', 'text/plain'), {})
                    media_type.setdefault("schema", {'type': 'string'})

                    model_field = response_model.get_model_field()
                    if model_field:
                        model_field_schema, _, _ = field_schema(
                            model_field, model_name_map=model_name_map, ref_prefix=REF_PREFIX
                        )
                        media_type['schema'] = model_field_schema

                http422 = str(HTTP_422_UNPROCESSABLE_ENTITY)
                if (parameters or self.route.route_parameter_model.body_resolver) and not any(
                        [
                            status in operation["responses"]
                            for status in [http422, "4XX", "default"]
                        ]
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

    def get_openapi_path(
            self,
            model_name_map: t.Dict[t.Union[t.Type[BaseModel], t.Type[Enum]], str],
            path_prefix: t.Optional[str] = None
    ):
        paths = {}
        _path, _security_schemes = self._get_openapi_path_object(model_name_map=model_name_map)
        if _path:
            route_path = (
                normalize_path(f'{path_prefix}/{self.route.path_format}')
                if path_prefix else self.route.path_format
            )
            paths.setdefault(route_path, {}).update(_path)
        return paths, _security_schemes




