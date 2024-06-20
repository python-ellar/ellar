from contextlib import asynccontextmanager

from ellar.app import AppFactory
from ellar.common import (
    Inject,
    get,
)
from ellar.core.connection import Request
from ellar.testing import Test, TestClient
from ellar.utils.importer import get_class_import

from .config import ConfigTrustHostConfigure
from .sample import ApplicationModule

test_module = Test.create_test_module(
    modules=(ApplicationModule,),
    config_module=get_class_import(ConfigTrustHostConfigure),
)


class TestStarletteCompatibility:
    def test_func_route(self):
        client = test_module.get_test_client()
        response = client.get("/func")
        assert response.status_code == 200
        assert response.text == "Hello, world!"

        response = client.head("/func")
        assert response.status_code == 200
        assert response.text == ""

    def test_async_route(self):
        client = test_module.get_test_client()
        response = client.get("/async")
        assert response.status_code == 200
        assert response.text == "Hello, world!"

    def test_class_route(self):
        client = test_module.get_test_client()
        response = client.get("/classbase/class")
        assert response.status_code == 200
        assert response.text == "Hello, world!"

    def test_mounted_route(self):
        client = test_module.get_test_client()
        response = client.get("/users/")
        assert response.status_code == 200
        assert response.text == "Hello, everyone!"

    def test_mounted_route_path_params(self):
        client = test_module.get_test_client()
        response = client.get("/users/tomchristie")
        assert response.status_code == 200
        assert response.text == "Hello, tomchristie!"

    def test_subdomain_route(self):
        client = test_module.get_test_client(base_url="https://foo.example.org/")

        response = client.get("/")
        assert response.status_code == 200
        assert response.text == "Subdomain: foo"

    def test_websocket_route(self):
        client = test_module.get_test_client()
        with client.websocket_connect("/ws") as session:
            text = session.receive_text()
            assert text == "Hello, world!"

    def test_400(self):
        client = test_module.get_test_client()
        response = client.get("/404")
        assert response.status_code == 404
        assert response.json() == {"detail": "Not Found"}

    def test_405(self):
        client = test_module.get_test_client()
        response = client.post("/func")
        assert response.status_code == 405
        assert response.json() == {"detail": "Custom message"}

        response = client.post("/classbase/class")
        assert response.status_code == 405
        assert response.json() == {"detail": "Custom message"}

    def test_500(self):
        client = test_module.get_test_client(raise_server_exceptions=False)
        response = client.get("/classbase/500")
        assert response.status_code == 500
        assert response.json() == {"detail": "Server Error"}

    def test_middleware(self):
        client = test_module.get_test_client(base_url="http://incorrecthost")
        response = client.get("/func")
        assert response.status_code == 400
        assert response.text == "Invalid host header"

    def test_app_async_cm_lifespan(self, test_client_factory):
        startup_complete = False
        cleanup_complete = False

        @asynccontextmanager
        async def lifespan(app):
            nonlocal startup_complete, cleanup_complete
            startup_complete = True
            yield
            cleanup_complete = True

        app = Test.create_test_module(
            config_module={"DEFAULT_LIFESPAN_HANDLER": lifespan}
        ).create_application()

        assert not startup_complete
        assert not cleanup_complete
        with test_client_factory(app):
            assert startup_complete
            assert not cleanup_complete
        assert startup_complete
        assert cleanup_complete

    def test_app_debug_return_html(self):
        @get("/")
        async def homepage(request: Inject[Request]):
            raise RuntimeError()

        app = AppFactory.create_app()
        app.router.add_route(homepage)
        app.debug = True

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/", headers={"accept": "text/html"})
        assert response.status_code == 500
        assert "<head>" in response.text
        assert ".traceback-container" in response.text
        assert app.debug

    def test_app_debug_plain_text(self):
        @get("/")
        async def homepage(request: Inject[Request]):
            raise RuntimeError()

        app = AppFactory.create_app()
        app.router.add_route(homepage)
        app.debug = True

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/")
        assert response.status_code == 500
        assert "test_starlette_compatibility.py" in response.text
        assert app.debug
