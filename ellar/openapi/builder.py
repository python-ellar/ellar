import typing as t
from enum import Enum

from pydantic import AnyUrl, BaseModel, EmailStr
from pydantic.fields import ModelField
from pydantic.schema import (
    TypeModelOrEnum,
    get_flat_models_from_fields,
    get_model_name_map,
    model_process_schema,
)
from starlette.routing import BaseRoute, Mount

from ellar.compatible import cached_property
from ellar.constants import GUARDS_KEY, OPENAPI_KEY
from ellar.core.main import App
from ellar.core.routing import ModuleMount, RouteOperation
from ellar.core.routing.controller.route import ControllerRouteOperation
from ellar.core.schema import HTTPValidationError, ValidationError
from ellar.helper.modelfield import create_model_field
from ellar.services.reflector import Reflector

from ..constants import REF_PREFIX
from .openapi_v3 import OpenAPI
from .route_doc_models import (
    OpenAPIMountDocumentation,
    OpenAPIRoute,
    OpenAPIRouteDocumentation,
)

default_openapi_version = "3.0.2"


class OpenAPIDocumentBuilder:
    def __init__(self) -> None:
        self._build: t.Dict = dict()
        self._build.setdefault("info", {}).update(
            title="Ellar API Docs", version="1.0.0"
        )
        self._build.setdefault("tags", [])
        self._build.setdefault("openapi", default_openapi_version)

    def set_openapi_version(self, openapi_version: str) -> "OpenAPIDocumentBuilder":
        """
        Sets OpenAPI version
        This is not fully supported yet
        :param openapi_version:
        :return: "OpenAPIDocumentBuilder"
        """
        self._build["openapi"] = openapi_version
        return self

    def set_title(self, title: str) -> "OpenAPIDocumentBuilder":
        self._build["info"]["title"] = title
        return self

    def set_version(self, version: str) -> "OpenAPIDocumentBuilder":
        self._build["info"]["version"] = version
        return self

    def set_description(self, description: str) -> "OpenAPIDocumentBuilder":
        self._build["info"]["description"] = description
        return self

    def set_term_of_service(self, term_of_service: str) -> "OpenAPIDocumentBuilder":
        self._build["info"]["termsOfService"] = term_of_service
        return self

    def set_contact(
        self,
        name: str,
        url: t.Optional[AnyUrl] = None,
        email: t.Optional[EmailStr] = None,
    ) -> "OpenAPIDocumentBuilder":
        self._build["info"]["contact"] = dict(name=name, url=url, email=email)
        return self

    def set_license(
        self, name: str, url: t.Optional[AnyUrl] = None
    ) -> "OpenAPIDocumentBuilder":
        self._build["info"]["license"] = dict(name=name, url=url)
        return self

    def set_external_doc(
        self, url: AnyUrl, description: t.Optional[str] = None
    ) -> "OpenAPIDocumentBuilder":
        self._build["externalDocs"] = dict(url=url, description=description)
        return self

    def add_server(
        self,
        url: t.Union[AnyUrl, str],
        description: t.Optional[str] = None,
        **variables: t.Dict[str, t.Union[str, t.List[str]]],
    ) -> "OpenAPIDocumentBuilder":
        self._build.setdefault("servers", []).append(
            dict(url=url, description=description, variables=variables)
        )
        return self

    def add_tags(
        self,
        name: str,
        description: t.Optional[str] = None,
        external_doc_url: t.Optional[AnyUrl] = None,
        external_doc_description: t.Optional[str] = None,
    ) -> "OpenAPIDocumentBuilder":
        data: t.Dict = dict(name=name, description=description)
        if external_doc_url:
            data["externalDocs"] = dict(
                description=external_doc_description, url=external_doc_url
            )
        self._build.setdefault("tags", []).append(data)
        return self

    def _get_openapi_route_document_models(self, app: App) -> t.List[OpenAPIRoute]:
        openapi_route_models: t.List = []
        reflector = app.injector.get(Reflector)
        for route in app.routes:
            if (
                isinstance(route, ModuleMount)
                and len(route.routes) > 0
                and route.include_in_schema
            ):
                openapi: t.Dict = dict()
                guards = reflector.get(GUARDS_KEY, route.get_control_type())
                app_guards = app.get_guards()

                openapi_route_models.append(
                    OpenAPIMountDocumentation(
                        mount=route, global_guards=guards or app_guards, **openapi
                    )
                )
            elif (
                isinstance(route, (RouteOperation, ControllerRouteOperation))
                and route.include_in_schema
            ):
                openapi = reflector.get(OPENAPI_KEY, route.endpoint) or dict()
                guards = reflector.get(GUARDS_KEY, route.endpoint) or app.get_guards()
                openapi_route_models.append(
                    OpenAPIRouteDocumentation(route=route, guards=guards, **openapi)
                )
        return openapi_route_models

    def _get_operations_models(
        self, routes: t.List[OpenAPIRoute]
    ) -> t.List[ModelField]:
        operation_models = []
        for route in routes:
            operation_models.extend(route.get_route_models())
        return operation_models

    def _get_model_definitions(
        self,
        *,
        models: t.List[ModelField],
        model_name_map: t.Dict[t.Union[t.Type[BaseModel], t.Type[Enum]], str],
    ) -> t.Dict[str, t.Any]:
        definitions: t.Dict[str, t.Any] = {}
        for model in models:
            _model: TypeModelOrEnum = t.cast(TypeModelOrEnum, model)
            m_schema, m_definitions, m_nested_models = model_process_schema(
                _model, model_name_map=model_name_map, ref_prefix=REF_PREFIX
            )
            definitions.update(m_definitions)
            model_name = model_name_map[_model]
            definitions[model_name] = m_schema
        return definitions

    @cached_property
    def error_model_fields(
        self,
    ) -> t.List[ModelField]:
        _model_fields = []
        for schema in [ValidationError, HTTPValidationError]:
            model_field = create_model_field(name=schema.__name__, type_=schema)
            _model_fields.append(model_field)
        return _model_fields

    def build_document(self, app: App) -> OpenAPI:
        openapi_route_models = self._get_openapi_route_document_models(app=app)
        components: t.Dict[str, t.Dict[str, t.Any]] = {}

        paths: t.Dict[str, t.Dict[str, t.Any]] = self._build.setdefault("paths", {})
        _flat_model = (
            self._get_operations_models(openapi_route_models) + self.error_model_fields
        )
        models = get_flat_models_from_fields(_flat_model, known_models=set())
        model_name_map = get_model_name_map(models)

        definitions = self._get_model_definitions(
            models=models, model_name_map=model_name_map  # type: ignore
        )
        mounts: t.List[t.Union[BaseRoute, ModuleMount, Mount]] = []
        for _, item in app.injector.get_templating_modules().items():
            mounts.extend(item.routers)

        for route in openapi_route_models:
            security_schemes: t.Dict[str, t.Any] = dict()
            route.get_openapi_path(
                model_name_map=model_name_map,
                paths=paths,
                security_schemes=security_schemes,
            )
            if security_schemes:
                components.setdefault("securitySchemes", {}).update(security_schemes)

        if definitions:
            components["schemas"] = {k: definitions[k] for k in sorted(definitions)}

        for route_model in openapi_route_models:
            if isinstance(route_model, OpenAPIMountDocumentation):
                data = route_model.get_tag()
                if data:
                    self._build.setdefault("tags", []).append(data)
        if components:
            self._build.setdefault("components", {}).update(components)
        return OpenAPI(**self._build)
