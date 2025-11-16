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

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.testing.dependency_analyzer import (
        ApplicationModuleDependencyAnalyzer,
        ControllerDependencyAnalyzer,
    )


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
        try:
            return t.cast(T, self.create_application().injector.get(interface))
        except Exception as ex:
            # try to find module to which the interface belongs
            module = self.create_application().injector.tree_manager.search_module_tree(
                filter_item=lambda data: True,
                find_predicate=lambda data: interface in data.exports
                or interface in data.providers,
            )
            if module:
                return t.cast(T, module.value.get(interface))

            raise ex


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
        application_module: t.Optional[t.Union[t.Type[ModuleBase], str]] = None,
        global_guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = None,
        config_module: t.Optional[t.Union[str, t.Dict]] = None,
    ) -> TESTING_MODULE:  # type: ignore[valid-type]
        """
        Create a TestingModule to test controllers and services in isolation

        :param controllers: Module Controllers
        :param routers: Module router
        :param providers: Module Services
        :param template_folder: Module Templating folder
        :param base_directory: Base Directory for static folder and template
        :param static_folder: Module Static folder
        :param modules: Other module dependencies
        :param application_module: Optional ApplicationModule to resolve dependencies from.
                                   Can be a module type or import string (e.g., "app.module:ApplicationModule")
        :param global_guards: Application Guard
        :param config_module: Application Config
        :return: TestingModule instance
        """

        # Convert to mutable list
        modules_list = list(modules)

        # If application_module provided, analyze and auto-register dependencies
        if application_module:
            from ellar.testing.dependency_analyzer import (
                ApplicationModuleDependencyAnalyzer,
                ControllerDependencyAnalyzer,
            )

            app_analyzer = ApplicationModuleDependencyAnalyzer(application_module)
            controller_analyzer = ControllerDependencyAnalyzer()

            # 1. Resolve ForwardRefs in registered modules
            resolved_modules = cls._resolve_forward_refs(modules_list, app_analyzer)
            modules_list = resolved_modules

            # 2. Analyze controllers and find required modules (with recursive dependencies)
            required_modules = cls._analyze_and_resolve_controller_dependencies(
                controllers, controller_analyzer, app_analyzer
            )

            # 3. Add required modules that aren't already registered
            # Use type comparison to avoid duplicates
            existing_module_types = {
                m if isinstance(m, type) else m.module if hasattr(m, "module") else m
                for m in modules_list
            }
            for required_module in required_modules:
                if required_module not in existing_module_types:
                    modules_list.append(required_module)
                    existing_module_types.add(required_module)

        # Create the module with complete dependency list
        module = Module(
            modules=modules_list,
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

    @classmethod
    def _resolve_forward_refs(
        cls,
        modules: t.List[t.Any],
        app_analyzer: "ApplicationModuleDependencyAnalyzer",
    ) -> t.List[t.Any]:
        """Resolve ForwardRefModule instances from ApplicationModule"""
        from ellar.core import ForwardRefModule

        resolved = []
        for module in modules:
            if isinstance(module, ForwardRefModule):
                actual_module = app_analyzer.resolve_forward_ref(module)
                if actual_module:
                    resolved.append(actual_module)
                else:
                    # Keep original if can't resolve (might be test-specific)
                    resolved.append(module)
            else:
                resolved.append(module)

        return resolved

    @classmethod
    def _analyze_and_resolve_controller_dependencies(
        cls,
        controllers: t.Sequence[t.Type[ControllerBase]],
        controller_analyzer: "ControllerDependencyAnalyzer",
        app_analyzer: "ApplicationModuleDependencyAnalyzer",
    ) -> t.List[t.Type[ModuleBase]]:
        """
        Find modules that provide services required by controllers

        This method finds direct modules that provide the required services.
        Nested module dependencies are automatically handled by Ellar's module system
        when AppFactory.read_all_module processes the modules.
        """
        required_modules = []
        required_modules_set = set()

        for controller in controllers:
            # Get dependencies from controller
            dependencies = controller_analyzer.get_dependencies(controller)

            # For each dependency, find the providing module
            for dep_type in dependencies:
                # Handle tagged dependencies (InjectByTag)
                # NewType creates callables with __supertype__ attribute
                if hasattr(dep_type, "__supertype__"):
                    resolved_type = app_analyzer.get_type_from_tag(dep_type)
                    if not resolved_type:
                        continue
                    dep_type = resolved_type

                providing_module = app_analyzer.find_module_providing_service(dep_type)

                if providing_module:
                    # Add only the direct providing module
                    # Nested dependencies will be handled by AppFactory.read_all_module
                    if providing_module not in required_modules_set:
                        required_modules.append(providing_module)
                        required_modules_set.add(providing_module)

        return required_modules
