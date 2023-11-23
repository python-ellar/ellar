import typing as t
from collections import OrderedDict
from pathlib import Path
from uuid import uuid4

from ellar.common import EllarTyper
from ellar.common.constants import MODULE_METADATA, MODULE_WATERMARK
from ellar.common.models import GuardCanActivate
from ellar.core.conf import Config
from ellar.core.modules import DynamicModule, ModuleBase, ModuleSetup
from ellar.di import EllarInjector, ProviderConfig
from ellar.reflect import reflect
from starlette.routing import Host, Mount

from .main import App
from .services import EllarAppService

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common.routing import ModuleMount, ModuleRouter


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
                module.apply_configuration()
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
        config: "Config",
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

        app_module_config = ModuleSetup(app_module)
        module_dependency = cls.get_all_modules(app_module_config)

        for module_config in reversed(module_dependency):
            if injector.get_module(module_config.module):  # pragma: no cover
                continue

            module_ref = module_config.get_module_ref(
                container=injector.container, config=config
            )

            # if not isinstance(module_ref, ModuleSetup):
            #     module_ref.run_module_register_services()

            injector.add_module(module_ref)

        for module_config in reversed(list(injector.get_dynamic_modules())):
            if injector.get_module(module_config.module):  # pragma: no cover
                continue

            module_ref = module_config.configure_with_factory(
                config, injector.container
            )
            # module_ref.run_module_register_services()

            injector.add_module(module_ref)

    @classmethod
    def _create_app(
        cls,
        module: t.Type[t.Union[ModuleBase, t.Any]],
        global_guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = None,
        config_module: t.Union[str, t.Dict, None] = None,
    ) -> App:
        def _get_config_kwargs() -> t.Dict:
            if config_module is None:
                return {}

            if not isinstance(config_module, (str, dict)):
                raise Exception(
                    "config_module should be a importable str or a dict object"
                )

            if isinstance(config_module, str):
                return {"config_module": config_module}
            return dict(config_module)

        assert reflect.get_metadata(MODULE_WATERMARK, module), "Only Module is allowed"

        config = Config(app_configured=True, **_get_config_kwargs())

        injector = EllarInjector(auto_bind=config.INJECTOR_AUTO_BIND)
        injector.container.register_instance(config, concrete_type=Config)

        service = EllarAppService(injector, config)
        service.register_core_services()

        cls._build_modules(app_module=module, injector=injector, config=config)

        app = App(
            config=config,
            injector=injector,
            lifespan=config.DEFAULT_LIFESPAN_HANDLER,
            global_guards=global_guards,
        )

        routes = []
        module_changed = False

        for module_config in reversed(list(injector.get_app_dependent_modules())):
            if injector.get_module(module_config.module):  # pragma: no cover
                continue

            module_ref = module_config.configure_with_factory(
                config, injector.container
            )
            # module_ref.run_module_register_services()

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
        controllers: t.Sequence[t.Union[t.Type]] = (),
        routers: t.Sequence[t.Union["ModuleRouter", "ModuleMount", Mount, Host]] = (),
        providers: t.Sequence[t.Union[t.Type, "ProviderConfig"]] = (),
        modules: t.Sequence[t.Type[t.Union[ModuleBase, t.Any]]] = (),
        template_folder: t.Optional[str] = None,
        base_directory: t.Optional[t.Union[str, Path]] = None,
        static_folder: str = "static",
        global_guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = None,
        commands: t.Sequence[t.Union[t.Callable, "EllarTyper"]] = (),
        config_module: t.Union[str, t.Dict, None] = None,
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
        app_factory_module = type(f"Module{uuid4().hex[:6]}", (), {})
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
        global_guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = None,
        config_module: t.Union[str, t.Dict, None] = None,
    ) -> App:
        return cls._create_app(
            module, config_module=config_module, global_guards=global_guards
        )
