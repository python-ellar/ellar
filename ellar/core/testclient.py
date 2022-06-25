import typing as t

from starlette.testclient import TestClient as TestClient

from ellar.constants import MODULE_METADATA, MODULE_WATERMARK
from ellar.core import ModuleBase
from ellar.core.factory import AppFactory
from ellar.core.main import App
from ellar.core.routing import ModuleRouter
from ellar.di import ProviderConfig
from ellar.reflect import reflect


class _TestingModule:
    def __init__(self, app: App) -> None:
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
        controllers: t.Sequence[t.Union[t.Any]] = tuple(),
        routers: t.Sequence[ModuleRouter] = tuple(),
        services: t.Sequence[ProviderConfig] = tuple(),
        template_folder: t.Optional[str] = None,
        base_directory: t.Optional[str] = None,
        static_folder: str = "static",
    ) -> _TestingModule:
        app = AppFactory.create_app(
            controllers=controllers,
            routers=routers,
            providers=services,
            template_folder=template_folder,
            base_directory=base_directory,
            static_folder=static_folder,
        )
        return _TestingModule(app=app)

    @classmethod
    def create_test_module_from_module(
        cls,
        module: t.Union[t.Type, t.Type[ModuleBase]],
        mock_services: t.Sequence[ProviderConfig] = tuple(),
    ) -> _TestingModule:
        app_module_watermark = reflect.get_metadata(MODULE_WATERMARK, module)
        if mock_services:
            reflect.define_metadata(
                MODULE_METADATA.PROVIDERS, list(mock_services), module, default_value=[]
            )

        if app_module_watermark:
            return _TestingModule(app=AppFactory.create_from_app_module(module))
        app = AppFactory.create_app(modules=(module,), providers=mock_services)
        return _TestingModule(app=app)
