import inspect
import typing as t
from pathlib import Path

from starlette.routing import BaseRoute

from architek.core.events import (
    ApplicationEventHandler,
    ApplicationEventManager,
    EventHandler,
    RouterEventManager,
)
from architek.core.guard import GuardCanActivate
from architek.core.routing import ModuleRouter, OperationDefinitions
from architek.core.routing.controller import ControllerDecorator
from architek.di import ProviderConfig
from architek.di.injector import Container
from architek.types import T

from .base import BaseModuleDecorator, ModuleBase, ModuleBaseMeta


class ModuleDecorator(BaseModuleDecorator):
    def __init__(
        self,
        *,
        name: t.Optional[str] = __name__,
        controllers: t.Sequence[ControllerDecorator] = tuple(),
        routers: t.Sequence[t.Union[ModuleRouter, OperationDefinitions]] = tuple(),
        services: t.Sequence[t.Union[t.Type, ProviderConfig]] = tuple(),
        template_folder: t.Optional[str] = None,
        base_directory: t.Optional[t.Union[Path, str]] = None,
        static_folder: str = "static",
    ):
        super().__init__()
        self.name = name
        self._controllers = [] if controllers is None else list(controllers)
        self._services: t.List[ProviderConfig] = []
        self._template_folder = template_folder
        self._static_folder = static_folder
        self._module_class: t.Optional[t.Type[ModuleBase]] = None
        self._module_base_directory = base_directory
        self._module_routers = self._get_module_routers(routers=routers)
        self._builder_service(services=services)
        self.on_startup = RouterEventManager()
        self.on_shutdown = RouterEventManager()
        self.before_initialisation = ApplicationEventManager()
        self.after_initialisation = ApplicationEventManager()

    def get_module(self) -> t.Type[ModuleBase]:
        assert self._module_class, "Module not properly configured"
        return self._module_class

    def __call__(self, module_class: t.Type) -> "ModuleDecorator":
        _module_class = t.cast(t.Type[ModuleBase], module_class)
        if type(_module_class) != ModuleBaseMeta:
            _module_class = type(
                module_class.__name__,
                (module_class, ModuleBase),
                {"_module_decorator": self},
            )
        self._module_class = _module_class
        self.resolve_module_base_directory(_module_class)
        return self

    def resolve_module_base_directory(self, module_class: t.Type[ModuleBase]) -> None:
        if not self._module_base_directory:
            self._module_base_directory = (
                Path(inspect.getfile(module_class)).resolve().parent
            )
        module_class._module_decorator = self

    def configure_module(self, container: Container) -> None:
        for _provider in self._services:
            _provider.register(container)

        for controller in self._controllers:
            ProviderConfig(controller.get_controller_type()).register(container)

    def _builder_service(
        self, services: t.Sequence[t.Union[t.Type, ProviderConfig]]
    ) -> None:
        for item in services:
            if not isinstance(item, ProviderConfig):
                self._services.append(ProviderConfig(item))
                continue
            self._services.append(item)

    def _build_routes(self) -> t.List[BaseRoute]:
        routes = list(self._module_routers)
        for controller in self._controllers:
            routes.append(controller.get_route())
        return routes

    @classmethod
    def _get_module_routers(
        cls, routers: t.Sequence[t.Union[ModuleRouter, OperationDefinitions]]
    ) -> t.List[BaseRoute]:
        results: t.List[BaseRoute] = []
        for item in routers:
            if isinstance(item, OperationDefinitions) and item.routes:
                results.extend(item.routes)  # type: ignore
                continue
            if isinstance(item, ModuleRouter):
                item.build_routes()
                results.append(item)
        return results


TAppModuleValue = t.Union[ModuleBase, BaseModuleDecorator]
TAppModule = t.Dict[t.Type[ModuleBase], TAppModuleValue]


class ApplicationModuleDecorator(ModuleDecorator):
    def __init__(
        self,
        *,
        controllers: t.Sequence[ControllerDecorator] = tuple(),
        routers: t.Sequence[t.Union[ModuleRouter, OperationDefinitions]] = tuple(),
        services: t.Sequence[t.Union[t.Type, ProviderConfig]] = tuple(),
        modules: t.Sequence[
            t.Union[t.Type, BaseModuleDecorator, ModuleDecorator]
        ] = tuple(),
        global_guards: t.List[
            t.Union[t.Type[GuardCanActivate], GuardCanActivate]
        ] = None,
        template_folder: t.Optional[str] = None,
        base_directory: t.Optional[t.Union[Path, str]] = None,
        static_folder: str = "static",
    ) -> None:
        super().__init__(
            controllers=controllers,
            services=services,
            template_folder=template_folder,
            base_directory=base_directory,
            static_folder=static_folder,
            routers=routers,
        )
        self._data: TAppModule = self._process_modules(modules)
        self._app_modules: t.List[t.Union[BaseModuleDecorator, ModuleDecorator]] = []
        self._global_guards = global_guards or []

    @property
    def global_guards(
        self,
    ) -> t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]]:
        return self._global_guards

    def __call__(self, module_class: t.Type) -> "ApplicationModuleDecorator":
        super().__call__(module_class)
        self._data.update(self._process_modules([self]))
        return self

    def __contains__(self, item: t.Type[ModuleBase]) -> bool:
        return item in self._data

    def configure_module(self, container: Container) -> None:
        super().configure_module(container=container)
        for module in self.modules(exclude_root=True):
            container.install(module)

    def _build_routes(self) -> t.List[BaseRoute]:
        routes = super()._build_routes()
        for module in self.modules(exclude_root=True):
            routes.extend(module._build_routes())
        return routes

    def get_startup_events(self) -> t.List[EventHandler]:
        events = list(self.on_startup)
        for module in self.modules(exclude_root=True):
            events.extend(module.on_startup)
        return events

    def get_shutdown_events(self) -> t.List[EventHandler]:
        events = list(self.on_shutdown)
        for module in self.modules(exclude_root=True):
            events.extend(module.on_shutdown)
        return events

    def get_before_events(self) -> t.List[ApplicationEventHandler]:
        events = list(self.before_initialisation)
        for module in self.modules(exclude_root=True):
            events.extend(module.before_initialisation)
        return events

    def get_after_events(self) -> t.List[ApplicationEventHandler]:
        events = list(self.after_initialisation)
        for module in self.modules(exclude_root=True):
            events.extend(module.after_initialisation)
        return events

    @classmethod
    def _process_modules(
        cls,
        modules: t.Sequence[t.Union[t.Type[ModuleBase], t.Type, BaseModuleDecorator]],
    ) -> TAppModule:
        _result: TAppModule = {}
        for module in modules:
            instance = module
            if type(module) == ModuleBaseMeta:
                _result[module] = module()
                continue

            if isinstance(module, ModuleBase):
                instance = type(module).get_module_decorator()
                _result[instance.get_module()] = instance
                continue

            if isinstance(instance, BaseModuleDecorator):
                _result[instance.get_module()] = instance

        return _result

    def modules(
        self, exclude_root: bool = False
    ) -> t.Iterator[t.Union[BaseModuleDecorator, ModuleDecorator]]:
        if not self._app_modules:
            for module in self._data.values():
                if isinstance(module, BaseModuleDecorator):
                    self._app_modules.append(module)

        for item in self._app_modules:
            if isinstance(item, ApplicationModuleDecorator) and exclude_root:
                continue
            yield item

    def add_module(
        self,
        container: Container,
        module: t.Union[t.Type[ModuleBase], BaseModuleDecorator, t.Type[T]],
        **init_kwargs: t.Any,
    ) -> t.Tuple[t.Union[ModuleBase, BaseModuleDecorator, T], bool]:
        if isinstance(module, BaseModuleDecorator) and module.get_module() in self:
            return module, False

        if module in self._data:
            return self._data.get(module), False  # type: ignore

        _module_instance = container.install(module=module, **init_kwargs)
        self._data.update(self._process_modules([_module_instance]))
        self._app_modules = []  # clear _app_modules cache
        return _module_instance, True
