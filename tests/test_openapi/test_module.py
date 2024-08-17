import os
import typing

import pytest
from ellar.app import AppFactory
from ellar.common import GuardCanActivate
from ellar.common.constants import GUARDS_KEY, MODULE_METADATA
from ellar.core import ExecutionContext
from ellar.core.modules.ref import ModuleTemplateRef
from ellar.di import injectable
from ellar.openapi import (
    OpenAPIDocumentBuilder,
    OpenAPIDocumentModule,
    ReDocUI,
    StopLightUI,
    SwaggerUI,
)
from ellar.openapi.module import AllowAnyGuard
from ellar.reflect import reflect
from ellar.testing import TestClient

EMPTY_OPENAPI_DOC = {
    "openapi": "3.1.0",
    "info": {"title": "Ellar API Docs", "version": "1.0.0"},
    "paths": {},
    "components": {
        "schemas": {
            "HTTPValidationError": {
                "properties": {
                    "detail": {
                        "items": {"$ref": "#/components/schemas/ValidationError"},
                        "type": "array",
                        "title": "Details",
                    }
                },
                "type": "object",
                "required": ["detail"],
                "title": "HTTPValidationError",
            },
            "ValidationError": {
                "properties": {
                    "loc": {
                        "items": {"type": "string"},
                        "type": "array",
                        "title": "Location",
                    },
                    "msg": {"type": "string", "title": "Message"},
                    "type": {"type": "string", "title": "Error Type"},
                },
                "type": "object",
                "required": ["loc", "msg", "type"],
                "title": "ValidationError",
            },
        }
    },
    "tags": [],
}


@injectable
class CustomDocsGuard(GuardCanActivate):
    detail: str = "Not Allowed"

    async def can_activate(self, context: ExecutionContext) -> bool:
        return False


def test_openapi_module_template_path_exist():
    app = AppFactory.create_app()
    document = OpenAPIDocumentBuilder().build_document(app)

    module = OpenAPIDocumentModule.setup(
        app=app,
        document=document,
        docs_ui=SwaggerUI(),
    )

    module_ref = typing.cast(ModuleTemplateRef, app.injector.get_module(module))
    path = module_ref.jinja_loader.searchpath[0]
    assert os.path.exists(path)

    list_of_html_contained_in_path = ["swagger.html", "redocs.html"]
    for item in os.listdir(path):
        if os.path.isfile(os.path.join(path, item)):
            list_of_html_contained_in_path.remove(item)
    assert len(list_of_html_contained_in_path) == 0


def test_openapi_module_with_openapi_url_doesnot_create_new_openapi_url():
    app = AppFactory.create_app()
    client = TestClient(app)
    document = OpenAPIDocumentBuilder().build_document(app)

    OpenAPIDocumentModule.setup(
        app=app,
        openapi_url="/openapi_url.json",
        document=document,
        docs_ui=SwaggerUI(),
    )
    res = client.get("/docs")
    assert res.status_code == 200
    assert "/openapi_url.json" in res.text


def test_openapi_module_creates_openapi_url():
    app = AppFactory.create_app()
    document = OpenAPIDocumentBuilder().build_document(app)
    OpenAPIDocumentModule.setup(app=app, document=document, docs_ui=SwaggerUI())

    client = TestClient(app)
    res = client.get("/docs")

    assert res.status_code == 200
    assert "/openapi.json" in res.text

    res = client.get("/openapi.json")
    assert res.status_code == 200
    document_json = res.json()
    assert document_json == EMPTY_OPENAPI_DOC


def test_openapi_module_creates_swagger_endpoint():
    app = AppFactory.create_app()
    document = OpenAPIDocumentBuilder().build_document(app)

    OpenAPIDocumentModule.setup(
        app=app,
        openapi_url="/openapi_url.json",
        document=document,
        docs_ui=SwaggerUI(title="Swagger Doc Test", path="docs-swagger-test"),
    )
    client = TestClient(app)
    response = client.get("docs-swagger-test")
    assert response.status_code == 200
    assert "Swagger Doc Test" in response.text
    assert "openapi_url.json" in response.text
    assert '<div id="swagger-ui"></div>' in response.text
    assert "const ui = SwaggerUIBundle({" in response.text


def test_openapi_module_creates_redocs_endpoint():
    app = AppFactory.create_app()
    document = OpenAPIDocumentBuilder().build_document(app)
    OpenAPIDocumentModule.setup(
        app=app,
        openapi_url="/openapi_url.json",
        document=document,
        docs_ui=ReDocUI(title="Redocs Doc Test", path="docs-redocs-test"),
    )
    client = TestClient(app)

    response = client.get("docs-redocs-test")
    assert response.status_code == 200

    assert "Redocs Doc Test" in response.text
    assert "openapi_url.json" in response.text
    assert '<redoc spec-url="/openapi_url.json"></redoc>' in response.text


def test_openapi_module_creates_stoplight_endpoint():
    app = AppFactory.create_app()
    document = OpenAPIDocumentBuilder().build_document(app)
    OpenAPIDocumentModule.setup(
        app=app,
        document=document,
        docs_ui=StopLightUI(
            title="StopLight", path="elements-path", config={"layout": "nav"}
        ),
    )
    client = TestClient(app)

    response = client.get("elements-path")
    assert response.status_code == 200

    assert "StopLight" in response.text
    assert 'apiDescriptionUrl="/openapi.json"' in response.text

    assert '"layout": "nav"' in response.text
    assert '"router": "hash"' in response.text
    assert "StopLight" in response.text


def test_openapi_module_with_route_guards():
    app = AppFactory.create_app(providers=[CustomDocsGuard])
    document = OpenAPIDocumentBuilder().build_document(app)

    module = OpenAPIDocumentModule.setup(
        app=app,
        document=document,
        guards=[CustomDocsGuard],
        docs_ui=(SwaggerUI(), ReDocUI(), StopLightUI()),
    )
    client = TestClient(app)

    routers = reflect.get_metadata(MODULE_METADATA.ROUTERS, module)
    guards = reflect.get_metadata(GUARDS_KEY, routers[0])
    assert len(guards) == 2
    assert AllowAnyGuard in guards

    response = client.get("openapi.json")
    assert response.status_code == 403
    assert response.json() == {"detail": "Not Allowed", "status_code": 403}

    response = client.get("docs")
    assert response.status_code == 403
    assert response.json() == {"detail": "Not Allowed", "status_code": 403}

    response = client.get("redoc")
    assert response.status_code == 403
    assert response.json() == {"detail": "Not Allowed", "status_code": 403}


def test_invalid_open_api_doc_setup():
    app = AppFactory.create_app(providers=[CustomDocsGuard])
    document = OpenAPIDocumentBuilder().build_document(app)
    with pytest.raises(Exception) as ex:
        OpenAPIDocumentModule.setup(
            app=app,
            document=document,
            guards=[CustomDocsGuard],
            docs_ui=(CustomDocsGuard(),),
        )
    assert str(ex.value) == "CustomDocsGuard must be of type `IDocumentationUIContext`"

    with pytest.raises(Exception) as ex:
        OpenAPIDocumentModule.setup(
            app=app,
            document=document,
            guards=[CustomDocsGuard],
            docs_ui=(CustomDocsGuard,),
        )
    assert str(ex.value) == "CustomDocsGuard must be of type `IDocumentationUIContext`"


def test_app_global_guard_blocks_openapi_doc_page():
    app = AppFactory.create_app(global_guards=[CustomDocsGuard])
    document = OpenAPIDocumentBuilder().build_document(app)
    client = TestClient(app)

    OpenAPIDocumentModule.setup(
        app=app,
        document=document,
        docs_ui=SwaggerUI(),
        allow_any=False,
    )
    response = client.get("/docs")

    assert response.status_code == 403
    assert response.json() == {"detail": "Not Allowed", "status_code": 403}

    module = OpenAPIDocumentModule.setup(
        app=app,
        document=document,
        docs_ui=SwaggerUI(),
        allow_any=False,
        guards=[CustomDocsGuard],
    )

    routers = reflect.get_metadata(MODULE_METADATA.ROUTERS, module)
    guards = reflect.get_metadata(GUARDS_KEY, routers[0])

    assert len(guards) == 1
    assert AllowAnyGuard not in guards


def test_lazy_openapi_document_build():
    app = AppFactory.create_app()
    document = OpenAPIDocumentBuilder()

    OpenAPIDocumentModule.setup(
        app=app,
        document=document,
        router_prefix="/api",
        docs_ui=SwaggerUI(),
        allow_any=False,
    )
    client = TestClient(app)
    response = client.get("/api/openapi.json")

    assert response.status_code == 200
    assert response.json() == EMPTY_OPENAPI_DOC
