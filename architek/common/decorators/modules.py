import typing as t
from pathlib import Path

from architek.core.guard import GuardCanActivate
from architek.core.modules import ArchitekApplicationModule, ArchitekModule, BaseModule
from architek.core.routing import (
    ArchitekRouter,
    ControllerDecorator,
    OperationDefinitions,
)
from architek.di import ProviderConfig


def Module(
    *,
    name: t.Optional[str] = None,
    controllers: t.Sequence[ControllerDecorator] = tuple(),
    routers: t.Sequence[t.Union[ArchitekRouter, OperationDefinitions]] = tuple(),
    providers: t.Sequence[t.Union[t.Type, ProviderConfig]] = tuple(),
    template_folder: t.Optional[str] = None,
    base_directory: t.Optional[t.Union[Path, str]] = None,
    static_folder: str = "static"
) -> t.Callable[[t.Any], ArchitekModule]:
    def _decorator(module_type: t.Any) -> ArchitekModule:
        return ArchitekModule(
            name=name,
            controllers=controllers,
            routers=routers,
            services=providers,
            template_folder=template_folder,
            base_directory=base_directory,
            static_folder=static_folder,
        )(module_type)

    return _decorator


def ApplicationModule(
    *,
    modules: t.Sequence[t.Union[t.Type, BaseModule, ArchitekModule]] = tuple(),
    global_guards: t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]] = None,
    controllers: t.Sequence[ControllerDecorator] = tuple(),
    routers: t.Sequence[t.Union[ArchitekRouter, OperationDefinitions]] = tuple(),
    providers: t.Sequence[t.Union[t.Type, ProviderConfig]] = tuple(),
    template_folder: t.Optional[str] = None,
    base_directory: t.Optional[t.Union[Path, str]] = None,
    static_folder: str = "static"
) -> t.Callable[[t.Any], ArchitekApplicationModule]:
    def _decorator(module_type: t.Any) -> ArchitekApplicationModule:
        return ArchitekApplicationModule(
            modules=modules,
            controllers=controllers,
            routers=routers,
            services=providers,
            template_folder=template_folder,
            base_directory=base_directory,
            static_folder=static_folder,
            global_guards=global_guards,
        )(module_type)

    return _decorator
