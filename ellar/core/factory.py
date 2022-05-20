import typing as t

from starlette.routing import Mount

from ellar.constants import APP_MODULE_KEY
from ellar.core import Config
from ellar.core.events import ApplicationEventManager
from ellar.core.main import App
from ellar.core.modules import (
    ApplicationModuleDecorator,
    BaseModuleDecorator,
    ModuleBase,
    ModuleDecorator,
)

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.routing import ModuleRouter
    from ellar.core.routing.controller import ControllerDecorator
    from ellar.di import ProviderConfig


class AppFactoryModule(ModuleBase):
    pass


class AppFactory:
    @classmethod
    def _create_app(
        cls, app_module: t.Union[ApplicationModuleDecorator, t.Type]
    ) -> App:
        assert isinstance(
            app_module, ApplicationModuleDecorator
        ), "Only ApplicationModule is allowed"

        config = Config(app_configured=True)
        config.update({APP_MODULE_KEY: app_module})

        modules_data = app_module.build()
        before = ApplicationEventManager(modules_data.before_init)
        before.run(config=config)

        app = App(
            config=config,
            routes=modules_data.routes,
            middleware=modules_data.middleware,
            exception_handlers=modules_data.exception_handlers,
            on_shutdown_event_handlers=modules_data.shutdown_event,
            on_startup_event_handlers=modules_data.startup_event,
            root_module=app_module,
            global_guards=list(app_module.global_guards),
        )
        app.injector.container.install(app_module.get_module())

        after = ApplicationEventManager(modules_data.after_init)
        after.run(application=app)
        return app

    @classmethod
    def create_app(
        cls,
        controllers: t.Sequence[t.Union["ControllerDecorator", t.Type]] = tuple(),
        routers: t.Sequence[t.Union["ModuleRouter", Mount]] = tuple(),
        services: t.Sequence[t.Union[t.Type, "ProviderConfig"]] = tuple(),
        modules: t.Union[
            t.Sequence[ModuleDecorator],
            t.Sequence[t.Type],
            t.Sequence[BaseModuleDecorator],
        ] = (),
        template_folder: t.Optional[str] = None,
        base_directory: t.Optional[str] = None,
        static_folder: str = "static",
    ) -> App:
        app_module = ApplicationModuleDecorator(
            controllers=controllers,
            routers=routers,
            services=services,
            template_folder=template_folder,
            base_directory=base_directory,
            static_folder=static_folder,
            modules=modules,
        )
        app_module(AppFactoryModule)
        return cls._create_app(app_module)

    @classmethod
    def create_from_app_module(
        cls, app_module: t.Union[ApplicationModuleDecorator, t.Type]
    ) -> App:
        return cls._create_app(app_module)
