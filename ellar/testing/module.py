import typing as t
from pathlib import Path
from uuid import uuid4

from ellar.app import App, AppFactory
from ellar.common import (
    ControllerBase,
    GuardCanActivate,
    Module,
    ModuleRouter,
    constants,
)
from ellar.common.types import T
from ellar.core import ModuleBase
from ellar.core.routing import EllarControllerMount
from ellar.di import ProviderConfig
from ellar.reflect import reflect
from starlette.routing import Host, Mount
from starlette.testclient import TestClient as TestClient


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
        self._app: t.Optional[App] = None

    @property
    def module(self) -> t.Type[ModuleBase]:
        return self._testing_module

    def override_provider(
        self,
        base_type: t.Union[t.Type[T], t.Type],
        *,
        use_value: t.Optional[T] = None,
        use_class: t.Optional[t.Union[t.Type[T], t.Any]] = None,
        core: bool = False,
        export: bool = True,
    ) -> "TestingModule":
        """
        Overrides Service at module level.
        Use this function before creating an application instance.
        """
        provider_config = ProviderConfig(
            base_type,
            use_class=use_class,
            use_value=use_value,
            export=export,
            core=core,
        )
        reflect.define_metadata(
            constants.MODULE_METADATA.PROVIDERS, [provider_config], self._testing_module
        )
        return self

    def create_application(self) -> App:
        if self._app:
            return self._app

        self._app = AppFactory.create_from_app_module(
            module=self._testing_module,
            global_guards=self._global_guards,
            config_module=self._config_module,
        )

        return self._app

    def get_test_client(
        self,
        base_url: str = "http://testserver",
        raise_server_exceptions: bool = True,
        root_path: str = "",
        backend: t.Literal["asyncio", "trio"] = "asyncio",
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
        routers: t.Sequence[
            t.Union[ModuleRouter, EllarControllerMount, Mount, Host, t.Callable]
        ] = (),
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
        :param modules: Other module dependencies
        :param controllers: Module Controllers
        :param routers: Module router
        :param providers: Module Services
        :param template_folder: Module Templating folder
        :param base_directory: Base Directory for static folder and template
        :param static_folder: Module Static folder
        :param config_module: Application Config
        :param global_guards: Application Guard
        :param modify_modules: Modifies Modules
        if setup or register_setup is used to avoid module sharing metadata between tests
        :return:
        """

        # if modify_modules:
        #
        #     def modifier_module(
        #         _module: t.Union[t.Type, t.Any],
        #     ) -> t.Union[t.Type, t.Any]:
        #         return Module(
        #             controllers=,
        #             routers=,
        #             providers=,
        #             template_folder=,
        #             base_directory=,
        #             static_folder=,
        #             modules=
        #         )(
        #             type(
        #                 f"{get_name(_module)}Modified_{uuid4().hex[:6]}", (_module,), {}
        #             )
        #         )
        #
        #     for module_ in modules:
        #         if isinstance(module_, (ModuleSetup, DynamicModule)):
        #             module_.module = modifier_module(module_.module)

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

    @classmethod
    def create_from_module(
        cls,
        module: t.Type[t.Union[ModuleBase, t.Any]],
        global_guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = None,
        config_module: t.Optional[t.Union[str, t.Dict]] = None,
    ) -> TESTING_MODULE:  # type: ignore[valid-type]
        """
        Create a TestingModule from a specific module for isolation test
        :param module: Root Module
        :param config_module: Application Config
        :param global_guards: Application Guard
        if setup or register_setup is used to avoid module sharing metadata between tests
        :return:
        """
        return cls.TESTING_MODULE(
            module, global_guards=global_guards, config_module=config_module
        )
