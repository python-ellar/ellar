import os

import pytest
from ellar.app import AppFactory
from ellar.common import GuardCanActivate
from ellar.common.constants import GUARDS_KEY
from ellar.core import Config, ExecutionContext
from ellar.core.modules.ref import create_module_ref_factor
from ellar.di import EllarInjector, injectable
from ellar.openapi import (
    OpenAPIDocumentBuilder,
    OpenAPIDocumentModule,
    ReDocsUI,
    SwaggerUI,
)
from ellar.openapi.module import AllowAnyGuard
from ellar.reflect import reflect
from ellar.testing import TestClient


@injectable
class CustomDocsGuard(GuardCanActivate):
    detail: str = "Not Allowed"

    async def can_activate(self, context: ExecutionContext) -> bool:
        return False


def test_openapi_module_template_path_exist():
    injector = EllarInjector()
    config = Config()
    module_ref = create_module_ref_factor(
        OpenAPIDocumentModule,
        container=injector.container,
        config=config,
    )
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

    module_config = OpenAPIDocumentModule.setup(
        openapi_url="/openapi_url.json",
        document=document,
        docs_ui=SwaggerUI(),
    )
    app.install_module(module_config)
    res = client.get("/docs")
    assert res.status_code == 200
    assert "/openapi_url.json" in res.text


def test_openapi_module_creates_openapi_url():
    app = AppFactory.create_app()
    document = OpenAPIDocumentBuilder().build_document(app)
    client = TestClient(app)

    module_config = OpenAPIDocumentModule.setup(document=document, docs_ui=SwaggerUI())
    app.install_module(module_config)
    res = client.get("/docs")

    assert res.status_code == 200
    assert "/openapi.json" in res.text

    res = client.get("/openapi.json")
    assert res.status_code == 200

    assert res.json() == {
        "openapi": "3.0.2",
        "info": {"title": "Ellar API Docs", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "HTTPValidationError": {
                    "title": "HTTPValidationError",
                    "required": ["detail"],
                    "type": "object",
                    "properties": {
                        "detail": {
                            "title": "Details",
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/ValidationError"},
                        }
                    },
                },
                "ValidationError": {
                    "title": "ValidationError",
                    "required": ["loc", "msg", "type"],
                    "type": "object",
                    "properties": {
                        "loc": {
                            "title": "Location",
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "msg": {"title": "Message", "type": "string"},
                        "type": {"title": "Error Type", "type": "string"},
                    },
                },
            }
        },
        "tags": [],
    }


def test_openapi_module_creates_swagger_endpoint():
    app = AppFactory.create_app()
    document = OpenAPIDocumentBuilder().build_document(app)

    module_config = OpenAPIDocumentModule.setup(
        openapi_url="/openapi_url.json",
        document=document,
        docs_ui=SwaggerUI(title="Swagger Doc Test", path="docs-swagger-test"),
    )
    app.install_module(module_config)
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
    module_config = OpenAPIDocumentModule.setup(
        openapi_url="/openapi_url.json",
        document=document,
        docs_ui=ReDocsUI(title="Redocs Doc Test", path="docs-redocs-test"),
    )
    app.install_module(module_config)
    client = TestClient(app)

    response = client.get("docs-redocs-test")
    assert response.status_code == 200

    assert "Redocs Doc Test" in response.text
    assert "openapi_url.json" in response.text
    assert '<redoc spec-url="/openapi_url.json"></redoc>' in response.text


def test_openapi_module_with_route_guards():
    app = AppFactory.create_app(providers=[CustomDocsGuard])
    document = OpenAPIDocumentBuilder().build_document(app)

    module_config = OpenAPIDocumentModule.setup(
        document=document,
        guards=[CustomDocsGuard],
        docs_ui=(SwaggerUI(), ReDocsUI()),
    )
    app.install_module(module_config)
    client = TestClient(app)

    guards = reflect.get_metadata(
        GUARDS_KEY, module_config.routers[0].get_control_type()
    )
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
            document=document,
            guards=[CustomDocsGuard],
            docs_ui=(CustomDocsGuard(),),
        )
    assert str(ex.value) == "CustomDocsGuard must be of type `IDocumentationUIContext`"

    with pytest.raises(Exception) as ex:
        OpenAPIDocumentModule.setup(
            document=document,
            guards=[CustomDocsGuard],
            docs_ui=(CustomDocsGuard,),
        )
    assert str(ex.value) == "CustomDocsGuard must be of type `IDocumentationUIContext`"


def test_app_global_guard_blocks_openapi_doc_page():
    app = AppFactory.create_app(global_guards=[CustomDocsGuard])
    document = OpenAPIDocumentBuilder().build_document(app)
    client = TestClient(app)

    module_config = OpenAPIDocumentModule.setup(
        document=document,
        docs_ui=SwaggerUI(),
        allow_any=False,
    )
    app.install_module(module_config)
    response = client.get("/docs")

    assert response.status_code == 403
    assert response.json() == {"detail": "Not Allowed", "status_code": 403}

    module_config = OpenAPIDocumentModule.setup(
        document=document,
        docs_ui=SwaggerUI(),
        allow_any=False,
        guards=[CustomDocsGuard],
    )
    app.install_module(module_config)

    guards = reflect.get_metadata(
        GUARDS_KEY, module_config.routers[0].get_control_type()
    )
    assert len(guards) == 1
    assert AllowAnyGuard not in guards
