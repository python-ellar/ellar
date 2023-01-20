import typing as t
from collections import OrderedDict
from pathlib import Path
from uuid import uuid4

from starlette.routing import Host, Mount

from ellar.constants import MODULE_METADATA, MODULE_WATERMARK
from ellar.core import Config
from ellar.core.main import App
from ellar.core.modules import ModuleBase
from ellar.core.modules.ref import create_module_ref_factor
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
    def get_all_modules(
        cls, module: t.Type[t.Union[ModuleBase, t.Any]]
    ) -> t.List[t.Type[ModuleBase]]:
        """
        Gets all registered modules from a particular module in their order of dependencies
        :param module: Module Type
        :return: t.List[t.Type[ModuleBase]]
        """
        module_dependency = [module] + list(cls.read_all_module(module).values())
        return module_dependency

    @classmethod
    def read_all_module(
        cls, module: t.Type[t.Union[ModuleBase, t.Any]]
    ) -> t.Dict[t.Type, t.Type[ModuleBase]]:
        """
        Retrieves all modules dependencies registered in another module
        :param module: Module Type
        :return: t.Dict[t.Type, t.Type[ModuleBase]]
        """
        modules = reflect.get_metadata(MODULE_METADATA.MODULES, module) or []
        module_dependency = OrderedDict()
        for module in modules:
            module_dependency[module] = module
            module_dependency.update(cls.read_all_module(module))
        return module_dependency

    @classmethod
    def _build_modules(
        cls,
        app_module: t.Type[t.Union[ModuleBase, t.Any]],
        config: Config,
        injector: EllarInjector,
    ) -> None:
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

        module_dependency = cls.get_all_modules(app_module)
        for module in reversed(module_dependency):
            if injector.get_module(module):  # pragma: no cover
                continue

            module_ref = create_module_ref_factor(
                module,
                container=injector.container,
                config=config,
            )
            injector.add_module(module_ref)

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

        CoreServiceRegistration(injector).register_all()
        injector.container.register_instance(config, concrete_type=Config)
        cls._build_modules(app_module=module, injector=injector, config=config)

        shutdown_event = config.ON_REQUEST_STARTUP
        startup_event = config.ON_REQUEST_SHUTDOWN

        app = App(
            config=config,
            injector=injector,
            on_shutdown_event_handlers=shutdown_event if shutdown_event else None,
            on_startup_event_handlers=startup_event if startup_event else None,
            lifespan=config.DEFAULT_LIFESPAN_HANDLER,
            global_guards=global_guards,
        )

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
