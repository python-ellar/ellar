import typing as t
from pathlib import Path

from starlette.testclient import TestClient as TestClient

from ellar.core import ModuleBase
from ellar.core.factory import AppFactory
from ellar.core.main import App
from ellar.core.routing import ModuleRouter
from ellar.di import ProviderConfig

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core import GuardCanActivate


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
        modules: t.Sequence[t.Union[t.Type, t.Any]] = tuple(),
        controllers: t.Sequence[t.Union[t.Any]] = tuple(),
        routers: t.Sequence[ModuleRouter] = tuple(),
        providers: t.Sequence[ProviderConfig] = tuple(),
        template_folder: t.Optional[str] = None,
        base_directory: t.Optional[t.Union[str, Path]] = None,
        static_folder: str = "static",
        global_guards: t.List[
            t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]
        ] = None,
        config_module: t.Union[str, t.Dict] = None,
    ) -> _TestingModule:
        """
        Create a TestingModule to test controllers and services in isolation
        :param modules:
        :param controllers:
        :param routers:
        :param providers:
        :param template_folder:
        :param base_directory:
        :param static_folder:
        :param config_module:
        :param global_guards:
        :return:
        """
        app = AppFactory.create_app(
            modules=modules,
            controllers=controllers,
            routers=routers,
            providers=providers,
            template_folder=template_folder,
            base_directory=base_directory,
            static_folder=static_folder,
            config_module=config_module,
            global_guards=global_guards,
        )
        return _TestingModule(app=app)

    @classmethod
    def create_test_module_from_module(
        cls,
        module: t.Union[t.Type, t.Type[ModuleBase]],
        mock_providers: t.Sequence[ProviderConfig] = tuple(),
        config_module: str = None,
    ) -> _TestingModule:
        """
        Create a TestingModule from an existing module
        """
        app = AppFactory.create_app(
            modules=(module,), providers=mock_providers, config_module=config_module
        )
        return _TestingModule(app=app)
