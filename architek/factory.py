import typing as t

from architek.main import ArchitekApp
from architek.module import (
    ApplicationModule,
    BaseModule,
    Module,
    StarletteAPIModuleBase,
)

if t.TYPE_CHECKING:
    from architek.controller import ControllerDecorator
    from architek.di import ProviderConfig
    from architek.routing import ModuleRouter, RouteDefinitions


class AppFactoryModule(StarletteAPIModuleBase):
    pass


class ArchitekAppFactory:
    @classmethod
    def _create_app(cls, app_module: t.Union[ApplicationModule, t.Type]) -> ArchitekApp:
        assert isinstance(
            app_module, ApplicationModule
        ), "Only ApplicationModule is allowed"

        app = ArchitekApp(module=app_module)
        return app

    @classmethod
    def create_app(
        cls,
        controllers: t.Sequence["ControllerDecorator"] = tuple(),
        routers: t.Sequence[t.Union["ModuleRouter", "RouteDefinitions"]] = tuple(),
        services: t.Sequence[t.Union[t.Type, "ProviderConfig"]] = tuple(),
        modules: t.Union[
            t.Sequence[Module], t.Sequence[t.Type], t.Sequence[BaseModule]
        ] = (),
        template_folder: t.Optional[str] = None,
        base_directory: t.Optional[str] = None,
        static_folder: str = "static",
    ) -> ArchitekApp:
        app_module = ApplicationModule(
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
        cls, app_module: t.Union[ApplicationModule, t.Type]
    ) -> ArchitekApp:
        return cls._create_app(app_module)
