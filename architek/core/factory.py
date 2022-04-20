import typing as t

from architek.core.main import ArchitekApp
from architek.core.modules import (
    ArchitekApplicationModule,
    ArchitekModule,
    BaseModule,
    ModuleBase,
)

if t.TYPE_CHECKING:
    from architek.core.routing import ArchitekRouter, OperationDefinitions
    from architek.core.routing.controller import ControllerDecorator
    from architek.di import ProviderConfig


class AppFactoryModule(ModuleBase):
    pass


class ArchitekAppFactory:
    @classmethod
    def _create_app(
        cls, app_module: t.Union[ArchitekApplicationModule, t.Type]
    ) -> ArchitekApp:
        assert isinstance(
            app_module, ArchitekApplicationModule
        ), "Only ApplicationModule is allowed"

        app = ArchitekApp(module=app_module)
        return app

    @classmethod
    def create_app(
        cls,
        controllers: t.Sequence["ControllerDecorator"] = tuple(),
        routers: t.Sequence[
            t.Union["ArchitekRouter", "OperationDefinitions"]
        ] = tuple(),
        services: t.Sequence[t.Union[t.Type, "ProviderConfig"]] = tuple(),
        modules: t.Union[
            t.Sequence[ArchitekModule], t.Sequence[t.Type], t.Sequence[BaseModule]
        ] = (),
        template_folder: t.Optional[str] = None,
        base_directory: t.Optional[str] = None,
        static_folder: str = "static",
    ) -> ArchitekApp:
        app_module = ArchitekApplicationModule(
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
        cls, app_module: t.Union[ArchitekApplicationModule, t.Type]
    ) -> ArchitekApp:
        return cls._create_app(app_module)
