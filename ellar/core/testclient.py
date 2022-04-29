import typing as t

from starlette.testclient import TestClient as TestClient

from ellar.core.factory import ArchitekAppFactory
from ellar.core.main import ArchitekApp
from ellar.core.modules import (
    ApplicationModuleDecorator,
    BaseModuleDecorator,
    ModuleDecorator,
)
from ellar.core.routing import ModuleRouter
from ellar.core.routing.controller import ControllerDecorator
from ellar.di import ProviderConfig


class _TestingModule:
    def __init__(self, app: ArchitekApp) -> None:
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
            app=self.app,
            base_url=base_url,
            raise_server_exceptions=raise_server_exceptions,
            backend=backend,
            backend_options=backend_options,
            root_path=root_path,
        )


class TestClientFactory:
    @classmethod
    def create_test_module(
        cls,
        controllers: t.Sequence[t.Union[ControllerDecorator, t.Any]] = tuple(),
        routers: t.Sequence[ModuleRouter] = tuple(),
        services: t.Sequence[ProviderConfig] = tuple(),
        template_folder: t.Optional[str] = None,
        base_directory: t.Optional[str] = None,
        static_folder: str = "static",
    ) -> _TestingModule:
        app = ArchitekAppFactory.create_app(
            controllers=controllers,
            routers=routers,
            services=services,
            template_folder=template_folder,
            base_directory=base_directory,
            static_folder=static_folder,
        )
        return _TestingModule(app=app)

    @classmethod
    def create_test_module_from_module(
        cls,
        module: t.Union[
            ModuleDecorator, ApplicationModuleDecorator, BaseModuleDecorator
        ],
        mock_services: t.Sequence[ProviderConfig] = tuple(),
    ) -> _TestingModule:
        if isinstance(module, ApplicationModuleDecorator):
            if mock_services:

                @module.after_initialisation
                def _register_services(application: ArchitekApp) -> None:
                    for service in mock_services:
                        if isinstance(service, ProviderConfig):
                            service.register(application.injector.container)

            return _TestingModule(app=ArchitekAppFactory.create_from_app_module(module))
        app = ArchitekAppFactory.create_app(modules=(module,), services=mock_services)
        return _TestingModule(app=app)
