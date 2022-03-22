import typing as t

from starlette.testclient import TestClient as TestClient  # noqa
from starletteapi.main import StarletteApp
from starletteapi.application import StarletteAppFactory
from starletteapi.controller import Controller
from starletteapi.di import ServiceConfig
from starletteapi.module import ApplicationModule, BaseModule
from starletteapi.routing import ModuleRouter


class _TestingModule:
    def __init__(self, app: StarletteApp) -> None:
        self.app = app

    def get_client(
        self,
        base_url: str = "http://testserver",
        raise_server_exceptions: bool = True,
        root_path: str = "",
        backend: str = "asyncio",
        backend_options: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> TestClient:
        return TestClient(
            app=self.app, base_url=base_url,
            raise_server_exceptions=raise_server_exceptions,
            backend=backend, backend_options=backend_options,
            root_path=root_path
        )


class TestClientFactory:
    @classmethod
    def create_test_module(
            cls,
            controllers: t.Sequence[t.Union[Controller, t.Any]] = tuple(),
            routers: t.Sequence[ModuleRouter] = tuple(),
            services: t.Sequence[ServiceConfig] = tuple(),
            template_folder: t.Optional[str] = None,
            base_directory: t.Optional[str] = None,
            static_folder: str = 'static',
    ) -> _TestingModule:
        app = StarletteAppFactory.create_app(
            controllers=controllers, routers=routers,
            services=services, template_folder=template_folder,
            base_directory=base_directory, static_folder=static_folder,
        )
        return _TestingModule(app=app)

    @classmethod
    def create_test_module_from_module(
            cls,
            module: t.Union[t.Type, BaseModule],
            mock_services: t.Sequence[ServiceConfig] = tuple(),
    ):
        if isinstance(module, ApplicationModule):
            if mock_services:
                @module.after_initialisation
                def _register_services(application: StarletteApp):
                    for service in mock_services:
                        if isinstance(service, ServiceConfig):
                            service.register(application.injector.container)

            return _TestingModule(app=StarletteApp(module))
        app = StarletteAppFactory.create_app(modules=(module,), services=mock_services)
        return _TestingModule(app=app)
