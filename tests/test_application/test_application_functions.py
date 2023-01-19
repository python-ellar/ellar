import os
import typing as t

from starlette.responses import JSONResponse, PlainTextResponse, Response

from ellar.common import Module, get, template_filter, template_global
from ellar.compatible import asynccontextmanager
from ellar.core import (
    App,
    AppFactory,
    Config,
    ModuleBase,
    TestClient,
    TestClientFactory,
)
from ellar.core.connection import Request
from ellar.core.context import IExecutionContext
from ellar.core.events import EventHandler
from ellar.core.exceptions.interfaces import IExceptionHandler
from ellar.core.modules import ModuleTemplateRef
from ellar.core.services import CoreServiceRegistration
from ellar.core.staticfiles import StaticFiles
from ellar.core.templating import Environment
from ellar.core.versioning import VERSIONING, DefaultAPIVersioning, UrlPathAPIVersioning
from ellar.di import EllarInjector
from ellar.helper.importer import get_class_import
from ellar.openapi import OpenAPIDocumentModule
from ellar.services.reflector import Reflector

from .config import ConfigTrustHostConfigure
from .sample import AppAPIKey, ApplicationModule

test_module = TestClientFactory.create_test_module_from_module(
    module=ApplicationModule, config_module=get_class_import(ConfigTrustHostConfigure)
)


class TestStarletteCompatibility:
    def test_func_route(self):
        client = test_module.get_client()
        response = client.get("/func")
        assert response.status_code == 200
        assert response.text == "Hello, world!"

        response = client.head("/func")
        assert response.status_code == 200
        assert response.text == ""

    def test_async_route(self):
        client = test_module.get_client()
        response = client.get("/async")
        assert response.status_code == 200
        assert response.text == "Hello, world!"

    def test_class_route(self):
        client = test_module.get_client()
        response = client.get("/classbase/class")
        assert response.status_code == 200
        assert response.text == "Hello, world!"

    def test_mounted_route(self):
        client = test_module.get_client()
        response = client.get("/users/")
        assert response.status_code == 200
        assert response.text == "Hello, everyone!"

    def test_mounted_route_path_params(self):
        client = test_module.get_client()
        response = client.get("/users/tomchristie")
        assert response.status_code == 200
        assert response.text == "Hello, tomchristie!"

    def test_subdomain_route(self):
        client = test_module.get_client(base_url="https://foo.example.org/")

        response = client.get("/")
        assert response.status_code == 200
        assert response.text == "Subdomain: foo"

    def test_websocket_route(self):
        client = test_module.get_client()
        with client.websocket_connect("/ws") as session:
            text = session.receive_text()
            assert text == "Hello, world!"

    def test_400(self):
        client = test_module.get_client()
        response = client.get("/404")
        assert response.status_code == 404
        assert response.json() == {"detail": "Not Found"}

    def test_405(self):
        client = test_module.get_client()
        response = client.post("/func")
        assert response.status_code == 405
        assert response.json() == {"detail": "Custom message"}

        response = client.post("/classbase/class")
        assert response.status_code == 405
        assert response.json() == {"detail": "Custom message"}

    def test_500(self):
        client = test_module.get_client(raise_server_exceptions=False)
        response = client.get("/classbase/500")
        assert response.status_code == 500
        assert response.json() == {"detail": "Server Error"}

    def test_middleware(self):
        client = test_module.get_client(base_url="http://incorrecthost")
        response = client.get("/func")
        assert response.status_code == 400
        assert response.text == "Invalid host header"

    def test_app_add_event_handler(self, test_client_factory):
        startup_complete = False
        cleanup_complete = False

        def run_startup():
            nonlocal startup_complete
            startup_complete = True

        def run_cleanup():
            nonlocal cleanup_complete
            cleanup_complete = True

        app = App(
            config=Config(),
            injector=EllarInjector(),
            on_startup_event_handlers=[EventHandler(run_startup)],
            on_shutdown_event_handlers=[EventHandler(run_cleanup)],
        )

        assert not startup_complete
        assert not cleanup_complete
        with test_client_factory(app):
            assert startup_complete
            assert not cleanup_complete
        assert startup_complete
        assert cleanup_complete

    def test_app_async_cm_lifespan(self, test_client_factory):
        startup_complete = False
        cleanup_complete = False

        @asynccontextmanager
        async def lifespan(app):
            nonlocal startup_complete, cleanup_complete
            startup_complete = True
            yield
            cleanup_complete = True

        app = App(config=Config(), injector=EllarInjector(), lifespan=lifespan)

        assert not startup_complete
        assert not cleanup_complete
        with test_client_factory(app):
            assert startup_complete
            assert not cleanup_complete
        assert startup_complete
        assert cleanup_complete

    def test_app_debug_return_html(self):
        @get("/")
        async def homepage(request: Request):
            raise RuntimeError()

        app = AppFactory.create_app()
        app.router.append(homepage)
        app.debug = True

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/", headers={"accept": "text/html"})
        assert response.status_code == 500
        assert "<head>" in response.text
        assert ".traceback-container" in response.text
        assert app.debug

    def test_app_debug_plain_text(self):
        @get("/")
        async def homepage(request: Request):
            raise RuntimeError()

        app = AppFactory.create_app()
        app.router.append(homepage)
        app.debug = True

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/")
        assert response.status_code == 500
        assert "test_application_functions.py" in response.text
        assert app.debug


class TestEllarApp:
    def test_ellar_as_asgi_app(self):
        @get("/")
        async def homepage(request: Request, ctx: IExecutionContext):
            res = PlainTextResponse("Ellar Route Handler as an ASGI app")
            await res(*ctx.get_args())

        app = AppFactory.create_app()
        app.router.append(homepage)
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        assert response.text == "Ellar Route Handler as an ASGI app"

    def test_app_staticfiles_route(self, tmpdir):
        path = os.path.join(tmpdir, "example.txt")
        with open(path, "w") as file:
            file.write("<file content>")

        config = Config(STATIC_DIRECTORIES=[tmpdir])
        injector = EllarInjector()
        CoreServiceRegistration(injector).register_all()
        injector.container.register_instance(config)
        app = App(injector=injector, config=config)
        client = TestClient(app)

        response = client.get("/static/example.txt")
        assert response.status_code == 200
        assert response.text == "<file content>"

        response = client.post("/static/example.txt")
        assert response.status_code == 405
        assert response.json() == {"detail": "Method Not Allowed", "status_code": 405}

    def test_app_staticfiles_with_different_static_path(self, tmpdir):
        path = os.path.join(tmpdir, "example.txt")
        with open(path, "w") as file:
            file.write("<file content>")

        config = Config(
            STATIC_MOUNT_PATH="/static-modified", STATIC_DIRECTORIES=[tmpdir]
        )
        injector = EllarInjector()
        CoreServiceRegistration(injector).register_all()
        injector.container.register_instance(config)
        app = App(injector=injector, config=config)
        client = TestClient(app)

        response = client.get("/static-modified/example.txt")
        assert response.status_code == 200
        assert response.text == "<file content>"

    def test_app_install_module(self):
        app = AppFactory.create_from_app_module(module=ApplicationModule)
        assert app.injector.get_module(OpenAPIDocumentModule) is None

        module_instance = app.install_module(OpenAPIDocumentModule)
        assert isinstance(module_instance, OpenAPIDocumentModule)
        assert app.injector.get_module(OpenAPIDocumentModule)

        module_instance2 = app.install_module(OpenAPIDocumentModule)
        assert module_instance is module_instance2

    def test_has_static_files(self, tmpdir):
        app = App(injector=EllarInjector(), config=Config())
        assert app.has_static_files is False

        config = Config(STATIC_DIRECTORIES=[tmpdir])
        app = App(injector=EllarInjector(), config=config)
        assert app.has_static_files

    def test_app_enable_versioning_and_versioning_scheme(self):
        app = App(injector=EllarInjector(), config=Config())
        assert app.config.VERSIONING_SCHEME
        assert isinstance(app.config.VERSIONING_SCHEME, DefaultAPIVersioning)

        app.enable_versioning(schema=VERSIONING.URL)
        assert isinstance(app.config.VERSIONING_SCHEME, UrlPathAPIVersioning)

    def test_app_get_guards_and_use_global_guards(self):
        app = AppFactory.create_app()

        assert app.get_guards() == []
        app.use_global_guards(AppAPIKey, AppAPIKey())

        guards = app.get_guards()
        assert len(guards) == 2

    def test_app_initialization_completion(self):
        config = Config()
        injector = EllarInjector(
            auto_bind=False
        )  # will raise an exception is service is not registered
        CoreServiceRegistration(injector).register_all()
        injector.container.register_instance(config)

        app = App(config=config, injector=injector)
        assert injector.get(Reflector)
        assert injector.get(Config) is config
        assert injector.get(Environment) is app.jinja_environment

    def test_app_exception_handler(self):
        class CustomException(Exception):
            pass

        class CustomExceptionHandler(IExceptionHandler):
            exception_type_or_code = CustomException

            async def catch(
                self, ctx: IExecutionContext, exc: t.Union[t.Any, Exception]
            ) -> t.Union[Response, t.Any]:
                return JSONResponse(dict(detail=str(exc)), status_code=404)

        config = Config()
        injector = EllarInjector(
            auto_bind=False
        )  # will raise an exception is service is not registered
        CoreServiceRegistration(injector).register_all()
        injector.container.register_instance(config)
        app = App(config=config, injector=injector)
        app.add_exception_handler(CustomExceptionHandler())

        @get("/404")
        def raise_custom_exception():
            raise CustomException("Raised an Exception")

        app.router.append(raise_custom_exception)
        client = TestClient(app)
        res = client.get("/404")
        assert res.status_code == 404
        assert res.json() == {"detail": "Raised an Exception"}


class TestAppTemplating:
    @Module(template_folder="some_template")
    class AppTemplateModuleTest(ModuleBase):
        @template_filter(name="app_filter")
        def template_filter_test(self, value):
            return f"new filter {value}"

        @template_global(name="app_global")
        def template_global_test(self, value):
            return f"new global {value}"

    def test_app_get_module_loaders(self):
        app = AppFactory.create_from_app_module(module=self.AppTemplateModuleTest)
        loaders = list(app.get_module_loaders())
        assert len(loaders) == 1
        module_ref = loaders[0]
        assert isinstance(module_ref, ModuleTemplateRef)
        assert isinstance(module_ref.get_module_instance(), self.AppTemplateModuleTest)

    def test_app_jinja_environment(self):
        app = AppFactory.create_from_app_module(module=self.AppTemplateModuleTest)
        assert isinstance(app.jinja_environment, Environment)

        assert "app_filter" in app.jinja_environment.filters
        assert "app_global" in app.jinja_environment.globals
        template = app.jinja_environment.from_string(
            """<html>global: {{app_global(2)}} filter: {{3 | app_filter}}</html>"""
        )
        result = template.render()
        assert result == "<html>global: new global 2 filter: new filter 3</html>"

    def test_app_create_static_app(self, tmpdir):
        path = os.path.join(tmpdir, "example.txt")
        with open(path, "w") as file:
            file.write("<file content>")

        config = Config(STATIC_DIRECTORIES=[tmpdir])
        app = App(injector=EllarInjector(), config=config)
        static_app = app.create_static_app()
        assert isinstance(static_app, StaticFiles)
        client = TestClient(static_app)

        res = client.get("/example.txt")
        assert res.status_code == 200
        assert res.text == "<file content>"

        assert isinstance(app._static_app, StaticFiles)

        client = TestClient(app._static_app)
        res = client.get("/example.txt")
        assert res.status_code == 200
        assert res.text == "<file content>"

    def test_app_reload_static_app(self, tmpdir):
        path = os.path.join(tmpdir, "example.txt")
        with open(path, "w") as file:
            file.write("<file content>")

        config = Config(STATIC_DIRECTORIES=[tmpdir])
        app = App(injector=EllarInjector(), config=config)
        static_app_old = app._static_app

        app.reload_static_app()

        assert static_app_old is not app._static_app
        client = TestClient(app._static_app)

        res = client.get("/example.txt")
        assert res.status_code == 200
        assert res.text == "<file content>"

    def test_app_template_filter(self):
        app = App(injector=EllarInjector(), config=Config())

        @app.template_filter()
        def square(value):
            return value * value

        @app.template_filter(name="triple")
        def triple_function(value):
            return value * value * value

        template = app.jinja_environment.from_string(
            """<html>filter square: {{2 | square}}, filter triple_function: {{3 | triple}}</html>"""
        )
        result = template.render()
        assert result == "<html>filter square: 4, filter triple_function: 27</html>"

        app.reload_static_app()

        template = app.jinja_environment.from_string(
            """<html>filter square: {{2 | square}}, filter triple_function: {{3 | triple}}</html>"""
        )
        result = template.render()
        assert result == "<html>filter square: 4, filter triple_function: 27</html>"

    def test_app_template_global(self):
        app = App(injector=EllarInjector(), config=Config())

        @app.template_global()
        def square(value):
            return value * value

        @app.template_global(name="triple")
        def triple_function(value):
            return value * value * value

        template = app.jinja_environment.from_string(
            """<html>filter square: {{square(2)}}, filter triple_function: {{triple(3)}}</html>"""
        )
        result = template.render()
        assert result == "<html>filter square: 4, filter triple_function: 27</html>"

        app.reload_static_app()

        template = app.jinja_environment.from_string(
            """<html>filter square: {{square(2)}}, filter triple_function: {{triple(3)}}</html>"""
        )
        result = template.render()
        assert result == "<html>filter square: 4, filter triple_function: 27</html>"
