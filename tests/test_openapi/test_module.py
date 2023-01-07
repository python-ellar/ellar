import os

from ellar.core import (
    AppFactory,
    Config,
    ExecutionContext,
    GuardCanActivate,
    TestClient,
)
from ellar.core.modules.ref import create_module_ref_factor
from ellar.di import EllarInjector
from ellar.openapi import OpenAPIDocumentBuilder, OpenAPIDocumentModule


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


def test_openapi_module_with_openapi_url_doesnot_exist_new_openapi_url():
    app = AppFactory.create_app()
    document = OpenAPIDocumentBuilder().build_document(app)

    module_instance = app.install_module(
        OpenAPIDocumentModule, openapi_url="/openapi_url.json", document=document
    )
    assert module_instance._openapi_url == "/openapi_url.json"


def test_openapi_module_creates_openapi_url():
    app = AppFactory.create_app()
    document = OpenAPIDocumentBuilder().build_document(app)

    module_instance = app.install_module(OpenAPIDocumentModule, document=document)
    assert module_instance._openapi_url == "/openapi.json"


def test_openapi_module_creates_swagger_endpoint():
    app = AppFactory.create_app()
    document = OpenAPIDocumentBuilder().build_document(app)

    module_instance = app.install_module(
        OpenAPIDocumentModule, document=document, openapi_url="/openapi_url.json"
    )

    module_instance.setup_swagger_doc(
        title="Swagger Doc Test", path="docs-swagger-test"
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

    module_instance = app.install_module(
        OpenAPIDocumentModule, document=document, openapi_url="/openapi_url.json"
    )

    module_instance.setup_redocs(title="Redocs Doc Test", path="docs-redocs-test")
    client = TestClient(app)
    response = client.get("docs-redocs-test")
    assert response.status_code == 200

    assert "Redocs Doc Test" in response.text
    assert "openapi_url.json" in response.text
    assert '<redoc spec-url="/openapi_url.json"></redoc>' in response.text


def test_openapi_module_with_route_guards():
    app = AppFactory.create_app(providers=[CustomDocsGuard])
    document = OpenAPIDocumentBuilder().build_document(app)

    module_instance = app.install_module(
        OpenAPIDocumentModule, document=document, guards=[CustomDocsGuard]
    )
    module_instance.setup_redocs()
    module_instance.setup_swagger_doc()
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
