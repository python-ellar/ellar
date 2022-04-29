import typing as t
from pathlib import Path

from ellar.core.guard import GuardCanActivate
from ellar.core.modules import (
    ApplicationModuleDecorator,
    BaseModuleDecorator,
    ModuleDecorator,
)
from ellar.core.routing import ControllerDecorator, ModuleRouter, OperationDefinitions
from ellar.di import ProviderConfig


def Module(
    *,
    name: t.Optional[str] = None,
    controllers: t.Sequence[ControllerDecorator] = tuple(),
    routers: t.Sequence[t.Union[ModuleRouter, OperationDefinitions]] = tuple(),
    providers: t.Sequence[t.Union[t.Type, ProviderConfig]] = tuple(),
    template_folder: t.Optional[str] = None,
    base_directory: t.Optional[t.Union[Path, str]] = None,
    static_folder: str = "static"
) -> ModuleDecorator:
    return ModuleDecorator(
        name=name,
        controllers=controllers,
        routers=routers,
        services=providers,
        template_folder=template_folder,
        base_directory=base_directory,
        static_folder=static_folder,
    )


def ApplicationModule(
    *,
    modules: t.Sequence[
        t.Union[t.Type, BaseModuleDecorator, ModuleDecorator]
    ] = tuple(),
    global_guards: t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]] = None,
    controllers: t.Sequence[ControllerDecorator] = tuple(),
    routers: t.Sequence[t.Union[ModuleRouter, OperationDefinitions]] = tuple(),
    providers: t.Sequence[t.Union[t.Type, ProviderConfig]] = tuple(),
    template_folder: t.Optional[str] = None,
    base_directory: t.Optional[t.Union[Path, str]] = None,
    static_folder: str = "static"
) -> ApplicationModuleDecorator:
    return ApplicationModuleDecorator(
        modules=modules,
        controllers=controllers,
        routers=routers,
        services=providers,
        template_folder=template_folder,
        base_directory=base_directory,
        static_folder=static_folder,
        global_guards=global_guards,
    )
