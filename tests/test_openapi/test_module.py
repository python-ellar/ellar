import os

import pytest

from ellar.core import AppFactory, Config, ExecutionContext, GuardCanActivate
from ellar.core.modules.ref import create_module_ref_factor
from ellar.di import EllarInjector
from ellar.openapi import (
    OpenAPIDocumentBuilder,
    OpenAPIDocumentModule,
    ReDocDocumentGenerator,
    SwaggerDocumentGenerator,
)
from ellar.testing import TestClient


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
        document_generator=SwaggerDocumentGenerator(),
    )
    app.install_module(module_config)
    res = client.get("/docs")
    assert res.status_code == 200
    assert "/openapi_url.json" in res.text


def test_openapi_module_creates_openapi_url():
    app = AppFactory.create_app()
    document = OpenAPIDocumentBuilder().build_document(app)
    client = TestClient(app)

    module_config = OpenAPIDocumentModule.setup(
        document=document, document_generator=SwaggerDocumentGenerator()
    )
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
        document_generator=SwaggerDocumentGenerator(
            title="Swagger Doc Test", path="docs-swagger-test"
        ),
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
        document_generator=ReDocDocumentGenerator(
            title="Redocs Doc Test", path="docs-redocs-test"
        ),
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
        document_generator=(SwaggerDocumentGenerator(), ReDocDocumentGenerator()),
    )
    app.install_module(module_config)
    client = TestClient(app)

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
            document_generator=(CustomDocsGuard(),),
        )
    assert str(ex.value) == "CustomDocsGuard must be of type `IDocumentationGenerator`"

    with pytest.raises(Exception) as ex:

        OpenAPIDocumentModule.setup(
            document=document,
            guards=[CustomDocsGuard],
            document_generator=(CustomDocsGuard,),
        )
    assert str(ex.value) == "CustomDocsGuard must be of type `IDocumentationGenerator`"
