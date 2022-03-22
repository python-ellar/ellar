import typing as t
from starletteapi.main import StarletteApp
from starletteapi.module import ApplicationModule, Module, BaseModule, StarletteAPIModuleBase

if t.TYPE_CHECKING:
    from starletteapi.routing import ModuleRouter, RouteDefinitions
    from starletteapi.controller import Controller
    from starletteapi.di import ServiceConfig


class AppFactoryModule(StarletteAPIModuleBase):
    pass


class StarletteAppFactory:
    @classmethod
    def _create_app(
            cls, app_module: t.Union[ApplicationModule, t.Type]
    ) -> StarletteApp:
        assert isinstance(app_module, ApplicationModule), "Only ApplicationModule is allowed"

        app = StarletteApp(module=app_module)
        return app

    @classmethod
    def create_app(
            cls,
            controllers: t.Sequence['Controller'] = tuple(),
            routers: t.Sequence[t.Union['ModuleRouter', 'RouteDefinitions']] = tuple(),
            services: t.Sequence[t.Union[t.Type, 'ServiceConfig']] = tuple(),
            modules: t.Union[t.Sequence[Module], t.Sequence[t.Type], t.Sequence[BaseModule]] = tuple(),
            template_folder: t.Optional[str] = None,
            base_directory: t.Optional[str] = None,
            static_folder: str = 'static',
    ) -> StarletteApp:
        app_module = ApplicationModule(
            controllers=controllers, routers=routers,
            services=services, template_folder=template_folder,
            base_directory=base_directory, static_folder=static_folder,
            modules=modules
        )
        app_module(AppFactoryModule)
        return cls._create_app(app_module)

    @classmethod
    def create_from_app_module(cls, app_module: t.Union[ApplicationModule, t.Type]) -> StarletteApp:
        return cls._create_app(app_module)
