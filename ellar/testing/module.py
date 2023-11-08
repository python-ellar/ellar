import typing as t
from pathlib import Path
from uuid import uuid4

from ellar.app import App, AppFactory
from ellar.common import ControllerBase, Module
from ellar.common.routing import ModuleMount, ModuleRouter
from ellar.common.types import T
from ellar.core import ModuleBase
from ellar.di import ProviderConfig
from starlette.routing import Host, Mount
from starlette.testclient import TestClient as TestClient

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common import GuardCanActivate


class TestingModule:
    def __init__(
        self,
        testing_module: t.Type[t.Union[ModuleBase, t.Any]],
        global_guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = None,
        config_module: t.Optional[t.Union[str, t.Dict]] = None,
    ) -> None:
        self._testing_module = testing_module
        self._config_module = config_module
        self._global_guards = global_guards
        self._providers: t.List[ProviderConfig] = []
        self._app: t.Optional[App] = None

    def override_provider(
        self,
        base_type: t.Union[t.Type[T], t.Type],
        *,
        use_value: t.Optional[T] = None,
        use_class: t.Optional[t.Union[t.Type[T], t.Any]] = None,
    ) -> "TestingModule":
        """
        Overrides Service at module level.
        Use this function before creating an application instance.
        """
        provider_config = ProviderConfig(
            base_type, use_class=use_class, use_value=use_value
        )
        self._providers.append(provider_config)
        return self

    def create_application(self) -> App:
        if self._app:
            return self._app
        self._app = AppFactory.create_app(
            modules=[self._testing_module],
            global_guards=self._global_guards,
            config_module=self._config_module,
            providers=self._providers,
        )

        for _, module_ref in self._app.injector.get_modules().items():
            # setup module just in case lifespan function will not be called during testing.
            module_ref.run_module_register_services()

        return self._app

    def get_test_client(
        self,
        base_url: str = "http://testserver",
        raise_server_exceptions: bool = True,
        root_path: str = "",
        backend: str = "asyncio",
        backend_options: t.Optional[t.Dict[str, t.Any]] = None,
        **kwargs: t.Any,
    ) -> TestClient:
        return TestClient(
            app=self.create_application(),
            base_url=base_url,
            raise_server_exceptions=raise_server_exceptions,
            backend=backend,
            backend_options=backend_options,
            root_path=root_path,
            **kwargs,
        )

    def get(self, interface: t.Type[T]) -> T:
        return self.create_application().injector.get(interface)  # type: ignore[no-any-return]


class Test:
    TESTING_MODULE = TestingModule

    @classmethod
    def create_test_module(
        cls,
        controllers: t.Sequence[t.Union[t.Type[ControllerBase], t.Type]] = (),
        routers: t.Sequence[t.Union[ModuleRouter, ModuleMount, Mount, Host]] = (),
        providers: t.Sequence[t.Union[t.Type, "ProviderConfig"]] = (),
        template_folder: t.Optional[str] = "templates",
        base_directory: t.Optional[t.Union[Path, str]] = None,
        static_folder: str = "static",
        modules: t.Sequence[t.Union[t.Type, t.Any]] = (),
        global_guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = None,
        config_module: t.Optional[t.Union[str, t.Dict]] = None,
    ) -> TESTING_MODULE:  # type: ignore[valid-type]
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
        module = Module(
            modules=modules,
            controllers=controllers,
            routers=routers,
            providers=providers,
            template_folder=template_folder,
            base_directory=base_directory,
            static_folder=static_folder,
        )
        testing_module = type(f"TestingModule_{uuid4().hex[:6]}", (ModuleBase,), {})
        module(testing_module)
        return cls.TESTING_MODULE(
            testing_module, global_guards=global_guards, config_module=config_module
        )
