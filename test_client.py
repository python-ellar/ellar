import typing as t

from starlette.testclient import TestClient as TestClient  # noqa

from starletteapi.application import StarletteAppFactory
from starletteapi.controller import Controller
from starletteapi.module import ServiceConfig, StarletteAPIModuleBase, ApplicationModule, BaseModule
from starletteapi.routing import ModuleRouter


class _TestFakeModule(StarletteAPIModuleBase):
    pass


class _TestingModule:
    def __init__(self, module: ApplicationModule) -> None:
        self.module = module

    def create_test_client(
        self,
        base_url: str = "http://testserver",
        raise_server_exceptions: bool = True,
        root_path: str = "",
        backend: str = "asyncio",
        backend_options: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> TestClient:
        app = StarletteAppFactory.create_app(self.module)
        return TestClient(
            app=app, base_url=base_url,
            raise_server_exceptions=raise_server_exceptions,
            backend=backend, backend_options=backend_options,
            root_path=root_path
        )


class TestClientFactory:
    @classmethod
    def create_testing_module(
            cls,
            controllers: t.Sequence[Controller] = tuple(),
            routers: t.Sequence[ModuleRouter] = tuple(),
            services: t.Sequence[t.Union[t.Type, ServiceConfig]] = tuple(),
            template_folder: t.Optional[str] = None,
            base_directory: t.Optional[str] = None,
            static_folder: str = 'static',
    ) -> _TestingModule:
        test_module = ApplicationModule(
            controllers=controllers, routers=routers,
            services=services, template_folder=template_folder,
            base_directory=base_directory, static_folder=static_folder,
        )
        test_module(_TestFakeModule)
        return _TestingModule(test_module)

    @classmethod
    def create_testing_module_from_module(cls, module: t.Union[t.Type, BaseModule]):
        if isinstance(module, ApplicationModule):
            return _TestingModule(module)
        test_module = ApplicationModule(modules=(module,))
        test_module(_TestFakeModule)
        return _TestingModule(test_module)
