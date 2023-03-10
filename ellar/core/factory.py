import typing as t
from collections import OrderedDict
from pathlib import Path
from uuid import uuid4

from starlette.routing import BaseRoute, Host, Mount

from ellar.constants import MODULE_METADATA, MODULE_WATERMARK
from ellar.core import Config
from ellar.core.main import App
from ellar.core.modules import DynamicModule, ModuleBase, ModuleSetup
from ellar.di import EllarInjector, ProviderConfig
from ellar.reflect import reflect

from .services import CoreServiceRegistration

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.commands import EllarTyper
    from ellar.core import GuardCanActivate
    from ellar.core.routing import ModuleMount, ModuleRouter


class AppFactory:
    """
    Factory for creating Ellar Application
    """

    @classmethod
    def get_all_modules(cls, module_config: ModuleSetup) -> t.List[ModuleSetup]:
        """
        Gets all registered modules from a particular module in their order of dependencies
        :param module_config: Module Type
        :return: t.List[t.Type[ModuleBase]]
        """
        module_dependency = [module_config] + list(
            cls.read_all_module(module_config).values()
        )
        return module_dependency

    @classmethod
    def read_all_module(cls, module_config: ModuleSetup) -> t.Dict[t.Type, ModuleSetup]:
        """
        Retrieves all modules dependencies registered in another module
        :param module_config: Module Type
        :return: t.Dict[t.Type, t.Type[ModuleBase]]
        """
        modules = (
            reflect.get_metadata(MODULE_METADATA.MODULES, module_config.module) or []
        )
        module_dependency = OrderedDict()
        for module in modules:
            if isinstance(module, DynamicModule):
                module_config = ModuleSetup(module.module)
            elif isinstance(module, ModuleSetup):
                module_config = module
            else:
                module_config = ModuleSetup(module)

            module_dependency[module_config.module] = module_config
            module_dependency.update(cls.read_all_module(module_config))
        return module_dependency

    @classmethod
    def _build_modules(
        cls,
        app_module: t.Type[t.Union[ModuleBase, t.Any]],
        config: Config,
        injector: EllarInjector,
    ) -> t.List[BaseRoute]:
        """
        builds application module and registers them to EllarInjector
        :param app_module: Root App Module
        :param config: App Configuration instance
        :param injector: App Injector instance
        :return: `None`
        """
        assert reflect.get_metadata(
            MODULE_WATERMARK, app_module
        ), "Only Module is allowed"

        app_module_config = ModuleSetup(app_module)
        module_dependency = cls.get_all_modules(app_module_config)
        routes = []

        for module_config in reversed(module_dependency):
            if injector.get_module(module_config.module):  # pragma: no cover
                continue

            module_ref = module_config.get_module_ref(
                container=injector.container, config=config
            )

            if not isinstance(module_ref, ModuleSetup):
                module_ref.run_module_register_services()
                routes.extend(module_ref.routes)

            injector.add_module(module_ref)

        for module_config in injector.get_dynamic_modules():
            if injector.get_module(module_config.module):  # pragma: no cover
                continue

            module_ref = module_config.configure_with_factory(
                config, injector.container
            )
            module_ref.run_module_register_services()

            injector.add_module(module_ref)
            routes.extend(module_ref.routes)
        return routes

    @classmethod
    def _create_app(
        cls,
        module: t.Type[t.Union[ModuleBase, t.Any]],
        global_guards: t.List[
            t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]
        ] = None,
        config_module: str = None,
    ) -> App:
        assert reflect.get_metadata(MODULE_WATERMARK, module), "Only Module is allowed"

        config = Config(app_configured=True, config_module=config_module)
        injector = EllarInjector(auto_bind=config.INJECTOR_AUTO_BIND)
        injector.container.register_instance(config, concrete_type=Config)
        CoreServiceRegistration(injector, config).register_all()

        routes = cls._build_modules(app_module=module, injector=injector, config=config)

        shutdown_event = config.ON_REQUEST_STARTUP
        startup_event = config.ON_REQUEST_SHUTDOWN

        app = App(
            config=config,
            injector=injector,
            routes=routes,
            on_shutdown_event_handlers=shutdown_event if shutdown_event else None,
            on_startup_event_handlers=startup_event if startup_event else None,
            lifespan=config.DEFAULT_LIFESPAN_HANDLER,
            global_guards=global_guards,
        )

        routes = []
        module_changed = False

        for module_config in injector.get_app_dependent_modules():
            if injector.get_module(module_config.module):  # pragma: no cover
                continue

            module_ref = module_config.configure_with_factory(
                config, injector.container
            )
            module_ref.run_module_register_services()

            injector.add_module(module_ref)
            routes.extend(module_ref.routes)
            module_changed = True

        if module_changed:
            app.router.extend(routes)
            app.reload_static_app()
            app.rebuild_middleware_stack()

        return app

    @classmethod
    def create_app(
        cls,
        controllers: t.Sequence[t.Union[t.Type]] = tuple(),
        routers: t.Sequence[
            t.Union["ModuleRouter", "ModuleMount", Mount, Host]
        ] = tuple(),
        providers: t.Sequence[t.Union[t.Type, "ProviderConfig"]] = tuple(),
        modules: t.Sequence[t.Type[t.Union[ModuleBase, t.Any]]] = tuple(),
        template_folder: t.Optional[str] = None,
        base_directory: t.Optional[t.Union[str, Path]] = None,
        static_folder: str = "static",
        global_guards: t.List[
            t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]
        ] = None,
        commands: t.Sequence[t.Union[t.Callable, "EllarTyper"]] = tuple(),
        config_module: str = None,
    ) -> App:
        from ellar.common import Module

        module = Module(
            controllers=controllers,
            routers=routers,
            providers=providers,
            template_folder=template_folder,
            base_directory=base_directory,
            static_folder=static_folder,
            modules=modules,
            commands=commands,
        )
        app_factory_module = type(f"Module{uuid4().hex[:6]}", (ModuleBase,), {})
        module(app_factory_module)
        return cls._create_app(
            module=app_factory_module,
            config_module=config_module,
            global_guards=global_guards,
        )

    @classmethod
    def create_from_app_module(
        cls,
        module: t.Type[t.Union[ModuleBase, t.Any]],
        global_guards: t.List[
            t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]
        ] = None,
        config_module: str = None,
    ) -> App:
        return cls._create_app(
            module, config_module=config_module, global_guards=global_guards
        )
