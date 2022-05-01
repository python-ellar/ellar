import typing as t

from ellar.core.main import App
from ellar.core.modules import (
    ApplicationModuleDecorator,
    BaseModuleDecorator,
    ModuleBase,
    ModuleDecorator,
)

if t.TYPE_CHECKING:
    from ellar.core.routing import ModuleRouter, Mount, OperationDefinitions
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

        app = App(module=app_module)
        return app

    @classmethod
    def create_app(
        cls,
        controllers: t.Sequence["ControllerDecorator"] = tuple(),
        routers: t.Sequence[
            t.Union["ModuleRouter", "OperationDefinitions", "Mount"]
        ] = tuple(),
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
