import typing as t
from collections import OrderedDict
from uuid import uuid4

from starlette.routing import Host, Mount

from ellar.constants import (
    MODULE_METADATA,
    MODULE_WATERMARK,
    ON_REQUEST_SHUTDOWN_KEY,
    ON_REQUEST_STARTUP_KEY,
)
from ellar.core import Config
from ellar.core.main import App
from ellar.core.modules import ModuleBase
from ellar.core.modules.ref import ModuleTemplateRef, create_module_ref_factor
from ellar.di import ProviderConfig, StarletteInjector
from ellar.reflect import reflect

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.routing import ModuleMount, ModuleRouter


class AppFactory:
    @classmethod
    def _read_all_module(
        cls, module: t.Type[ModuleBase]
    ) -> t.Dict[t.Type, t.Type[ModuleBase]]:
        modules = reflect.get_metadata(MODULE_METADATA.MODULES, module) or []
        module_dependency = OrderedDict()
        for module in modules:
            module_dependency[module] = module
            module_dependency.update(cls._read_all_module(module))
        return module_dependency

    @classmethod
    def _build_modules(
        cls, app_module: t.Type[ModuleBase], config: Config, injector: StarletteInjector
    ) -> None:
        assert reflect.get_metadata(
            MODULE_WATERMARK, app_module
        ), "Only ApplicationModule is allowed"

        module_dependency = [app_module] + list(
            cls._read_all_module(app_module).values()
        )
        for module in reversed(module_dependency):
            if injector.get_module(module):
                continue

            module_ref = create_module_ref_factor(
                module,
                container=injector.container,
                config=config,
            )
            injector.add_module(module_ref)

    @classmethod
    def _run_module_application_ready(
        cls,
        modules: t.Dict[t.Type[ModuleBase], ModuleTemplateRef],
        app: App,
    ) -> None:
        for _, module_ref in modules.items():
            module_ref.run_application_ready(app)

    @classmethod
    def _create_app(cls, module: t.Type[ModuleBase], config_module: str = None) -> App:
        assert reflect.get_metadata(MODULE_WATERMARK, module), "Only Module is allowed"

        config = Config(app_configured=True, config_module=config_module)
        injector = StarletteInjector(auto_bind=t.cast(bool, config.INJECTOR_AUTO_BIND))
        cls._build_modules(app_module=module, injector=injector, config=config)

        shutdown_event = config[ON_REQUEST_STARTUP_KEY]
        startup_event = config[ON_REQUEST_SHUTDOWN_KEY]

        app = App(
            config=config,
            injector=injector,
            on_shutdown_event_handlers=shutdown_event if shutdown_event else None,
            on_startup_event_handlers=startup_event if startup_event else None,
            lifespan=t.cast(
                t.Optional[t.Callable[[App], t.AsyncContextManager[t.Any]]],
                config.DEFAULT_LIFESPAN_HANDLER,
            ),
        )

        cls._run_module_application_ready(
            modules=injector.get_templating_modules(), app=app
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
        modules: t.Sequence[t.Type] = (),
        template_folder: t.Optional[str] = None,
        base_directory: t.Optional[str] = None,
        static_folder: str = "static",
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
        )
        app_factory_module = type(f"Module{uuid4().hex[:6]}", (ModuleBase,), {})
        module(app_factory_module)
        return cls._create_app(
            t.cast(t.Type[ModuleBase], app_factory_module), config_module
        )

    @classmethod
    def create_from_app_module(
        cls, module: t.Type[ModuleBase], config_module: str = None
    ) -> App:
        return cls._create_app(module, config_module)
