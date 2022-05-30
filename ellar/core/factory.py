import typing as t
from uuid import uuid4

from starlette.routing import BaseRoute, Mount

from ellar.constants import (
    APP_MODULE_METADATA,
    APP_MODULE_WATERMARK,
    MODULE_WATERMARK,
    ON_REQUEST_SHUTDOWN_KEY,
    ON_REQUEST_STARTUP_KEY,
)
from ellar.core import Config
from ellar.core.main import App
from ellar.core.modules import ModuleBase
from ellar.core.modules.ref import ModulePlainRef, ModuleTemplateRef
from ellar.di import ProviderConfig, StarletteInjector
from ellar.reflect import reflect

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.routing import ModuleRouter


class AppFactory:
    @classmethod
    def _build_modules(
        cls, app_module: t.Type[ModuleBase], config: Config, injector: StarletteInjector
    ) -> None:
        assert reflect.get_metadata(
            APP_MODULE_WATERMARK, app_module
        ), "Only ApplicationModule is allowed"

        modules = reflect.get_metadata(APP_MODULE_METADATA.MODULES, app_module) or []
        module_dependency = [app_module] + list(modules)
        for module in reversed(module_dependency):
            if injector.get_module(module):
                continue

            if reflect.get_metadata(MODULE_WATERMARK, module) or reflect.get_metadata(
                APP_MODULE_WATERMARK, module
            ):
                module_ref = ModuleTemplateRef(
                    module, container=injector.container, config=config
                )
            else:
                module_ref = ModulePlainRef(
                    module, container=injector.container, config=config
                )
            injector.add_module(module_ref)

    @classmethod
    def _register_modules_services_and_get_routes(
        cls,
        modules: t.Dict[t.Type[ModuleBase], t.Union[ModulePlainRef, ModuleTemplateRef]],
    ) -> t.List[BaseRoute]:
        module_ref_routes = []
        for _, module_ref in modules.items():
            module_ref.run_module_register_services()
            module_ref_routes.extend(module_ref.routes)
        return module_ref_routes

    @classmethod
    def _run_module_application_ready(
        cls,
        modules: t.Dict[t.Type[ModuleBase], t.Union[ModulePlainRef, ModuleTemplateRef]],
        app: App,
    ) -> None:
        for _, module_ref in modules.items():
            module_ref.run_application_ready(app)

    @classmethod
    def _create_app(cls, module: t.Type[ModuleBase], config_module: str = None) -> App:
        assert reflect.get_metadata(
            APP_MODULE_WATERMARK, module
        ), "Only ApplicationModule is allowed"

        config = Config(app_configured=True, config_module=config_module)
        injector = StarletteInjector()
        cls._build_modules(app_module=module, injector=injector, config=config)
        routes = cls._register_modules_services_and_get_routes(
            modules=injector.get_modules()
        )
        shutdown_event = config[ON_REQUEST_STARTUP_KEY]
        startup_event = config[ON_REQUEST_SHUTDOWN_KEY]

        app = App(
            config=config,
            injector=injector,
            routes=routes,
            on_shutdown_event_handlers=shutdown_event if shutdown_event else None,
            on_startup_event_handlers=startup_event if startup_event else None,
            lifespan=config.DEFAULT_LIFESPAN_HANDLER,
        )

        cls._run_module_application_ready(modules=injector.get_modules(), app=app)
        return app

    @classmethod
    def create_app(
        cls,
        controllers: t.Sequence[t.Union[t.Type]] = tuple(),
        routers: t.Sequence[t.Union["ModuleRouter", Mount]] = tuple(),
        providers: t.Sequence[t.Union[t.Type, "ProviderConfig"]] = tuple(),
        modules: t.Sequence[t.Type] = (),
        template_folder: t.Optional[str] = None,
        base_directory: t.Optional[str] = None,
        static_folder: str = "static",
        config_module: str = None,
    ) -> App:
        from ellar.common import ApplicationModule

        module = ApplicationModule(
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
