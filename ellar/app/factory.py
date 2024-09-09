import typing as t
from pathlib import Path

from ellar.common import IApplicationReady, Module
from ellar.common.constants import MODULE_METADATA
from ellar.common.exceptions import ImproperConfiguration
from ellar.common.models import GuardCanActivate
from ellar.core import (
    Config,
    DynamicModule,
    ForwardRefModule,
    LazyModuleImport,
    ModuleBase,
    ModuleSetup,
)
from ellar.core.execution_context import injector_context
from ellar.core.module import get_core_module
from ellar.core.modules import ModuleRefBase, ModuleTemplateRef
from ellar.di import EllarInjector, ProviderConfig
from ellar.di.injector.tree_manager import ModuleTreeManager
from ellar.reflect import reflect
from ellar.threading.sync_worker import execute_async_context_manager, execute_coroutine
from ellar.utils import get_unique_type
from starlette.routing import Host, Mount

from ..events.build import build_with_context_event
from .main import App

if t.TYPE_CHECKING:  # pragma: no cover
    import click
    from ellar.common import ModuleRouter
    from ellar.core.routing import EllarControllerMount


class AppFactory:
    """
    Factory for creating Ellar Application
    """

    @classmethod
    def read_all_module(
        cls,
        module_config: t.Union[ModuleSetup, ModuleRefBase],
        tree_manager: t.Optional[ModuleTreeManager] = None,
    ) -> ModuleTreeManager:
        """
        Retrieves all module dependencies registered in another module

        :param tree_manager: Module Tree Manager
        :param module_config: Module Type
        :return: t.Dict[t.Type, t.Type[ModuleBase]]
        """
        global_module_config = module_config
        tree_manager = tree_manager or ModuleTreeManager().add_module(
            global_module_config.module, value=module_config
        )

        modules = (
            reflect.get_metadata(MODULE_METADATA.MODULES, module_config.module) or []
        )
        for module in modules:
            if isinstance(module, ForwardRefModule):
                # will be initialized using module_config moduleRef setup
                continue

            if isinstance(module, LazyModuleImport):
                module = module.get_module(global_module_config.module.__name__)

            if isinstance(module, DynamicModule):
                module.apply_configuration()
                module_config = ModuleSetup(module.module)
            elif isinstance(module, ModuleSetup):
                module_config = module
            else:
                module_config = ModuleSetup(module)

            tree_manager.add_module(
                module_type=module_config.module,
                value=module_config,
                parent_module=global_module_config.module,
            )

            cls.read_all_module(module_config, tree_manager)
        return tree_manager

    @classmethod
    @t.no_type_check
    def _create_app(
        cls,
        module: t.Type[t.Union[ModuleBase, t.Any]],
        global_guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = None,
        config_module: t.Union[str, t.Dict, None] = None,
        injector: t.Optional[EllarInjector] = None,
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

        config = Config(app_configured=True, **_get_config_kwargs())
        config.GLOBAL_GUARDS += list(global_guards or [])

        # injector = EllarInjector(auto_bind=config.INJECTOR_AUTO_BIND, parent=injector)
        # injector.container.register_instance(config, concrete_type=Config)

        core_module_ref = ModuleTemplateRef(
            module_type=get_core_module(module, config),
            parent_container=injector.container if injector else None,
            config=config,
        )
        with execute_async_context_manager(
            injector_context(core_module_ref.container.injector)
        ) as context:
            core_module_ref.initiate_module_build()

            tree_manager: ModuleTreeManager = core_module_ref.get(ModuleTreeManager)
            cls.read_all_module(core_module_ref, tree_manager)

            # service = EllarAppService(injector, config)
            # service.register_core_services()

            # Build application first level. This will trigger ApplicationModule to be built
            core_module_ref.build_dependencies(step=1)
            app_module_ref = tree_manager.get_app_module()

            app = App(
                routes=[],
                config=config,
                injector=app_module_ref.container.injector,
                lifespan=config.DEFAULT_LIFESPAN_HANDLER,
            )
            # tag application instance by ApplicationModule name
            core_module_ref.add_provider(
                ProviderConfig(App, use_value=app, tag="App", export=True)
            )
            app_module_ref.build_dependencies()

            routes = core_module_ref.get_routes()
            app.router.extend(routes)

            for item in config.OVERRIDE_CORE_SERVICE:
                provider_type = item.get_type()
                if provider_type not in core_module_ref.providers:
                    raise ImproperConfiguration(
                        f"There is not core service identify as {provider_type}"
                    )

                core_module_ref.add_provider(item, export=True)

            # app.setup_jinja_environment
            app.setup_jinja_environment()
            core_module_ref.run_module_register_services()

            for module in context.tree_manager.modules.keys():
                if issubclass(module, IApplicationReady):
                    context.get(module).on_ready(app)

            execute_coroutine(build_with_context_event.run())
            build_with_context_event.disconnect_all()

        return app

    @classmethod
    def create_app(
        cls,
        controllers: t.Sequence[t.Union[t.Type]] = (),
        routers: t.Sequence[
            t.Union["ModuleRouter", "EllarControllerMount", Mount, Host, t.Callable]
        ] = (),
        providers: t.Sequence[t.Union[t.Type, "ProviderConfig"]] = (),
        modules: t.Sequence[t.Type[t.Union[ModuleBase, t.Any]]] = (),
        template_folder: t.Optional[str] = None,
        base_directory: t.Optional[t.Union[str, Path]] = None,
        static_folder: str = "static",
        global_guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = None,
        commands: t.Sequence[t.Union["click.Command", "click.Group", t.Any]] = (),
        config_module: t.Union[str, t.Dict, None] = None,
        injector: t.Optional[EllarInjector] = None,
    ) -> App:
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
        app_factory_module = get_unique_type()
        module(app_factory_module)
        app = cls._create_app(
            module=app_factory_module,
            config_module=config_module,
            global_guards=global_guards,
            injector=injector,
        )
        return t.cast(App, app)

    @classmethod
    def create_from_app_module(
        cls,
        module: t.Type[t.Union[ModuleBase, t.Any]],
        global_guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = None,
        injector: t.Optional[EllarInjector] = None,
        config_module: t.Union[str, t.Dict, None] = None,
    ) -> App:
        app = cls._create_app(
            module,
            config_module=config_module,
            global_guards=global_guards,
            injector=injector,
        )

        return t.cast(App, app)
