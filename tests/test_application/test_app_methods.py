import os
import typing as t

from ellar.app import App, AppFactory
from ellar.app.services import EllarAppService
from ellar.common import (
    IExceptionHandler,
    IExecutionContext,
    Inject,
    get,
)
from ellar.common.templating import Environment
from ellar.core import Config
from ellar.core.connection import Request
from ellar.core.services.reflector import Reflector
from ellar.core.versioning import (
    UrlPathAPIVersioning,
)
from ellar.core.versioning import (
    VersioningSchemes as VERSIONING,
)
from ellar.di import EllarInjector
from ellar.testing import Test, TestClient
from starlette.responses import JSONResponse, PlainTextResponse, Response

from .sample import AppAPIKey


class TestEllarApp:
    def test_ellar_as_asgi_app(self):
        @get("/")
        async def homepage(request: Inject[Request], ctx: Inject[IExecutionContext]):
            res = PlainTextResponse("Ellar Route Handler as an ASGI app")
            await res(*ctx.get_args())

        app = AppFactory.create_app()
        app.router.add_route(homepage)
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        assert response.text == "Ellar Route Handler as an ASGI app"

    def test_ellar_app_url_for(self):
        @get("/homepage-url", name="homepage")
        async def homepage(request: Inject[Request], ctx: Inject[IExecutionContext]):
            res = PlainTextResponse("Ellar Route Handler as an ASGI app")
            return res

        app = AppFactory.create_app()
        app.router.add_route(homepage)
        result = app.url_path_for("homepage")
        assert result == "/homepage-url"

    def test_app_staticfiles_route(self, tmpdir):
        path = os.path.join(tmpdir, "example.txt")
        with open(path, "w") as file:
            file.write("<file content>")

        config = Config(STATIC_DIRECTORIES=[tmpdir])
        injector = EllarInjector()
        EllarAppService(injector, config=Config()).register_core_services()
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
        EllarAppService(injector, config=Config()).register_core_services()
        injector.container.register_instance(config)
        app = App(injector=injector, config=config)
        client = TestClient(app)

        response = client.get("/static-modified/example.txt")
        assert response.status_code == 200
        assert response.text == "<file content>"

    # def test_app_install_module(self):
    #     app = AppFactory.create_from_app_module(module=ApplicationModule)
    #     assert app.injector.get_module(OpenAPIDocumentModule) is None
    #
    #     module_instance = app.install_module(OpenAPIDocumentModule)
    #     assert isinstance(module_instance, OpenAPIDocumentModule)
    #     assert app.injector.get_module(OpenAPIDocumentModule)
    #
    #     module_instance2 = app.install_module(OpenAPIDocumentModule)
    #     assert module_instance is module_instance2

    def test_app_enable_versioning_and_versioning_scheme(self):
        app = Test.create_test_module().create_application()
        assert app.config.VERSIONING_SCHEME is None
        # assert isinstance(app.config.VERSIONING_SCHEME, DefaultAPIVersioning)

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
        EllarAppService(injector, config=Config()).register_core_services()
        injector.container.register_instance(config)

        app = App(config=config, injector=injector)
        app.setup_jinja_environment()
        assert injector.get(Reflector)
        assert injector.get(Config) is config
        assert injector.get(Environment)

    def test_app_exception_handler(self):
        class CustomException(Exception):
            pass

        class CustomExceptionHandler(IExceptionHandler):
            exception_type_or_code = CustomException

            async def catch(
                self, ctx: IExecutionContext, exc: t.Union[t.Any, Exception]
            ) -> t.Union[Response, t.Any]:
                return JSONResponse({"detail": str(exc)}, status_code=404)

        config = Config()
        injector = EllarInjector(
            auto_bind=False
        )  # will raise an exception is service is not registered
        EllarAppService(injector, config=Config()).register_core_services()
        injector.container.register_instance(config)
        app = App(config=config, injector=injector)
        app.add_exception_handler(CustomExceptionHandler())

        @get("/404")
        def raise_custom_exception():
            raise CustomException("Raised an Exception")

        app.router.add_route(raise_custom_exception)
        client = TestClient(app)
        res = client.get("/404")
        assert res.status_code == 404
        assert res.json() == {"detail": "Raised an Exception"}
