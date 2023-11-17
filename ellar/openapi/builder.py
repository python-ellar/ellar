import typing as t
from enum import Enum

from ellar.common import IIdentitySchemes
from ellar.common.compatible import AttributeDict, cached_property
from ellar.common.constants import GUARDS_KEY, REF_PREFIX
from ellar.common.routing import ModuleMount, RouteOperation
from ellar.common.routing.controller import ControllerRouteOperation
from ellar.common.utils.modelfield import create_model_field
from ellar.openapi.constants import OPENAPI_OPERATION_KEY, OPENAPI_TAG
from pydantic import AnyUrl, BaseModel, EmailStr
from pydantic.fields import ModelField
from pydantic.schema import (
    TypeModelOrEnum,
    get_flat_models_from_fields,
    get_model_name_map,
    model_process_schema,
)
from starlette.routing import BaseRoute, Mount

from .openapi_v3 import APIKeyIn, OpenAPI
from .route_doc_models import (
    OpenAPIMountDocumentation,
    OpenAPIRoute,
    OpenAPIRouteDocumentation,
)
from .schemas import HTTPValidationError, ValidationError

if t.TYPE_CHECKING:
    from ellar.app import App


default_openapi_version = "3.0.2"


class OpenAPIDocumentBuilderAction:
    def __init__(self, document_dict: t.Dict) -> None:
        self._build = document_dict

    def _get_openapi_route_document_models(self, app: "App") -> t.List[OpenAPIRoute]:
        openapi_route_models: t.List = []
        reflector = app.reflector
        app_guards = list(app.get_guards())

        for route in app.routes:
            if (
                isinstance(route, ModuleMount)
                and len(route.routes) > 0
                and route.include_in_schema
            ):
                openapi_tags = AttributeDict(
                    reflector.get(OPENAPI_TAG, route.get_control_type()) or {}
                )
                if route.name:
                    openapi_tags.setdefault("name", route.name)

                guards = reflector.get(GUARDS_KEY, route.get_control_type())

                openapi_route_models.append(
                    OpenAPIMountDocumentation(
                        mount=route,
                        global_guards=guards or app_guards,
                        name=openapi_tags.name,
                    )
                )
                if openapi_tags:
                    self._build.setdefault("tags", []).append(openapi_tags)
            elif (
                isinstance(route, (RouteOperation, ControllerRouteOperation))
                and route.include_in_schema
            ):
                openapi = reflector.get(OPENAPI_OPERATION_KEY, route.endpoint) or {}
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

    def build(self, app: "App") -> OpenAPI:
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
            security_schemes: t.Dict[str, t.Any] = {}
            route.get_openapi_path(
                model_name_map=model_name_map,
                paths=paths,
                security_schemes=security_schemes,
            )
            if security_schemes:
                components.setdefault("securitySchemes", {}).update(security_schemes)

        identity_schemes = app.injector.get(IIdentitySchemes)
        for auth in identity_schemes.get_authentication_schemes():
            security_scheme = auth.openapi_security_scheme()
            if security_scheme:
                components.setdefault("securitySchemes", {}).update(security_scheme)
                # scheme_name = list(security_scheme.keys())[0]
                # self._build.setdefault("security", []).append(
                #     {scheme_name: getattr(auth, "openapi_scope", [])}
                # )

        if definitions:
            components["schemas"] = {k: definitions[k] for k in sorted(definitions)}

        if components:
            self._build.setdefault("components", {}).update(components)
        return OpenAPI(**self._build)


class OpenAPIDocumentBuilder:
    _build_action_class: t.Type[
        OpenAPIDocumentBuilderAction
    ] = OpenAPIDocumentBuilderAction

    def __init__(self) -> None:
        self._build: t.Dict = {}
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
        url: t.Optional[t.Union[AnyUrl, str]] = None,
        email: t.Optional[t.Union[EmailStr, str]] = None,
    ) -> "OpenAPIDocumentBuilder":
        self._build["info"]["contact"] = {"name": name, "url": url, "email": email}
        return self

    def set_license(
        self, name: str, url: t.Optional[t.Union[AnyUrl, str]] = None
    ) -> "OpenAPIDocumentBuilder":
        self._build["info"]["license"] = {"name": name, "url": url}
        return self

    def set_external_doc(
        self, url: AnyUrl, description: t.Optional[str] = None
    ) -> "OpenAPIDocumentBuilder":
        self._build["externalDocs"] = {"url": url, "description": description}
        return self

    def add_server(
        self,
        url: t.Union[AnyUrl, str],
        description: t.Optional[str] = None,
        **variables: t.Dict[str, t.Union[str, t.List[str]]],
    ) -> "OpenAPIDocumentBuilder":
        self._build.setdefault("servers", []).append(
            {"url": url, "description": description, "variables": variables}
        )
        return self

    def add_tags(
        self,
        name: str,
        description: t.Optional[str] = None,
        external_doc_url: t.Optional[t.Union[AnyUrl, str]] = None,
        external_doc_description: t.Optional[str] = None,
    ) -> "OpenAPIDocumentBuilder":
        data: t.Dict = {"name": name, "description": description}
        if external_doc_url:
            data["externalDocs"] = {
                "description": external_doc_description,
                "url": external_doc_url,
            }
        self._build.setdefault("tags", []).append(data)
        return self

    def add_security_requirements(
        self, name: str, requirements: t.List[str]
    ) -> "OpenAPIDocumentBuilder":
        self._build.setdefault("security", []).append({name: requirements})
        return self

    def add_security(self, name: str, options: t.Dict) -> "OpenAPIDocumentBuilder":
        self._build.setdefault("components", {}).setdefault(
            "securitySchemes", {}
        ).update({name: options})
        return self

    def add_api_key(
        self,
        openapi_in: APIKeyIn,
        openapi_description: t.Optional[str] = None,
        name: str = "api_key",
    ) -> "OpenAPIDocumentBuilder":
        return self.add_security(
            name=name,
            options={
                "type": "apiKey",
                "description": openapi_description,
                "in": openapi_in.value,
                "name": name,
            },
        )

    def add_basic_auth(
        self,
        openapi_scheme: str = "basic",
        openapi_description: t.Optional[str] = None,
        name: str = "basic",
    ) -> "OpenAPIDocumentBuilder":
        return self.add_security(
            name=name,
            options={
                "type": "http",
                "description": openapi_description,
                "scheme": openapi_scheme,
                "name": name,
            },
        )

    def add_bearer_auth(
        self,
        openapi_description: t.Optional[str] = None,
        name: str = "bearer",
        bearer_format: str = "JWT",
    ) -> "OpenAPIDocumentBuilder":
        return self.add_security(
            name=name,
            options={
                "type": "http",
                "description": openapi_description,
                "scheme": "bearer",
                "bearerFormat": bearer_format,
                "name": name,
            },
        )

    def add_cookie_auth(
        self,
        cookie_name: str,
        openapi_description: t.Optional[str] = None,
        security_name: str = "cookie",
    ) -> "OpenAPIDocumentBuilder":
        return self.add_security(
            name=security_name,
            options={
                "type": "apiKey",
                "description": openapi_description,
                "in": APIKeyIn.cookie.value,
                "name": cookie_name,
            },
        )

    def build_document(self, app: "App") -> OpenAPI:
        build_action = self._build_action_class(document_dict=self._build)
        return build_action.build(app)
