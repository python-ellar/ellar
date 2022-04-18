import inspect
import typing as t
from abc import ABC, ABCMeta, abstractmethod
from pathlib import Path

from injector import Module as _InjectorModule
from starlette.routing import BaseRoute

from architek.controller import ControllerDecorator
from architek.di import ProviderConfig
from architek.di.injector import Container
from architek.events import (
    ApplicationEventHandler,
    ApplicationEventManager,
    EventHandler,
    RouterEventManager,
)
from architek.guard import GuardCanActivate
from architek.routing import ModuleRouter, RouteDefinitions
from architek.templating.interface import ModuleTemplating
from architek.types import T


def _configure_module(func: t.Callable) -> t.Any:
    def _configure_module_wrapper(self: t.Any, container: Container) -> t.Any:
        _module_decorator = getattr(self, "_module_decorator", None)
        if _module_decorator:
            _module_decorator = t.cast(Module, self._module_decorator)
            _module_decorator.configure_module(container=container)
        result = func(self, container=container)
        return result

    return _configure_module_wrapper


class StarletteAPIModuleBaseMeta(ABCMeta):
    _module_decorator: t.Optional["Module"]

    @t.no_type_check
    def __new__(mcls, name, bases, namespace, **kwargs):
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)
        cls._module_decorator = namespace.get("_module_decorator", None)
        return cls

    def get_module_decorator(cls) -> t.Optional["Module"]:
        return cls._module_decorator


class StarletteAPIModuleBase(_InjectorModule, metaclass=StarletteAPIModuleBaseMeta):
    def register_services(self, container: Container) -> None:
        """Register other services manually"""

    @_configure_module
    def configure(self, container: Container) -> None:
        self.register_services(container=container)


class BaseModule(ModuleTemplating, ABC, metaclass=ABCMeta):
    on_startup: RouterEventManager
    on_shutdown: RouterEventManager
    before_initialisation: ApplicationEventManager
    after_initialisation: ApplicationEventManager

    def __init__(self) -> None:
        self._routes: t.List[BaseRoute] = []

    @abstractmethod
    def get_module(self) -> t.Type[StarletteAPIModuleBase]:
        """decorated module class"""

    def get_routes(self, force_build: bool = False) -> t.List[BaseRoute]:
        if not force_build and self._routes:
            return self._routes
        self._routes = self._build_routes()
        return self._routes

    @abstractmethod
    def _build_routes(self) -> t.List[BaseRoute]:
        """build module controller routes"""


class Module(BaseModule):
    def __init__(
        self,
        *,
        name: t.Optional[str] = __name__,
        controllers: t.Sequence[ControllerDecorator] = tuple(),
        routers: t.Sequence[t.Union[ModuleRouter, RouteDefinitions]] = tuple(),
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
        self._module_class: t.Optional[t.Type[StarletteAPIModuleBase]] = None
        self._module_base_directory = base_directory
        self._module_routers = self._get_module_routers(routers=routers)
        self._builder_service(services=services)
        self.on_startup = RouterEventManager()
        self.on_shutdown = RouterEventManager()
        self.before_initialisation = ApplicationEventManager()
        self.after_initialisation = ApplicationEventManager()

    def get_module(self) -> t.Type[StarletteAPIModuleBase]:
        assert self._module_class, "Module not properly configured"
        return self._module_class

    def __call__(self, module_class: t.Type) -> "Module":
        _module_class = t.cast(t.Type[StarletteAPIModuleBase], module_class)
        if type(_module_class) != StarletteAPIModuleBaseMeta:
            _module_class = type(
                module_class.__name__,
                (module_class, StarletteAPIModuleBase),
                {"_module_decorator": self},
            )
        self._module_class = _module_class
        self.resolve_module_base_directory(_module_class)
        return self

    def resolve_module_base_directory(
        self, module_class: t.Type[StarletteAPIModuleBase]
    ) -> None:
        if not self._module_base_directory:
            self._module_base_directory = (
                Path(inspect.getfile(module_class)).resolve().parent
            )
        module_class._module_decorator = self

    def configure_module(self, container: Container) -> None:
        for _provider in self._services:
            _provider.register(container)

        for controller in self._controllers:
            container.add_exact_scoped(concrete_type=controller.get_controller_type())

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
        cls, routers: t.Sequence[t.Union[ModuleRouter, RouteDefinitions]]
    ) -> t.List[BaseRoute]:
        results: t.List[BaseRoute] = []
        for item in routers:
            if isinstance(item, RouteDefinitions):
                results.extend(item.routes)
                continue
            if isinstance(item, ModuleRouter):
                item.build_routes()
                results.append(item)
        return results


TAppModuleValue = t.Union[StarletteAPIModuleBase, BaseModule]
TAppModule = t.Dict[t.Type[StarletteAPIModuleBase], TAppModuleValue]


class ApplicationModule(Module):
    def __init__(
        self,
        *,
        controllers: t.Sequence[ControllerDecorator] = tuple(),
        routers: t.Sequence[t.Union[ModuleRouter, RouteDefinitions]] = tuple(),
        services: t.Sequence[t.Union[t.Type, ProviderConfig]] = tuple(),
        modules: t.Union[
            t.Sequence[Module], t.Sequence[t.Type], t.Sequence[BaseModule]
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
        self._app_modules: t.List[t.Union[BaseModule, Module]] = []
        self._global_guards = global_guards or []

    @property
    def global_guards(
        self,
    ) -> t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]]:
        return self._global_guards

    def __call__(self, module_class: t.Type) -> "ApplicationModule":
        super().__call__(module_class)
        self._data.update(self._process_modules([self]))
        return self

    def __contains__(self, item: t.Type[StarletteAPIModuleBase]) -> bool:
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
        modules: t.Sequence[
            t.Union[t.Type[StarletteAPIModuleBase], t.Type, BaseModule]
        ],
    ) -> TAppModule:
        _result: TAppModule = {}
        for module in modules:
            instance = module
            if type(module) == StarletteAPIModuleBaseMeta:
                _result[module] = module()
                continue

            if isinstance(module, StarletteAPIModuleBase):
                instance = type(module).get_module_decorator()
                _result[instance.get_module()] = instance
                continue

            if isinstance(instance, BaseModule):
                _result[instance.get_module()] = instance

        return _result

    def modules(
        self, exclude_root: bool = False
    ) -> t.Iterator[t.Union[BaseModule, Module]]:
        if not self._app_modules:
            for module in self._data.values():
                if isinstance(module, BaseModule):
                    self._app_modules.append(module)

        for item in self._app_modules:
            if isinstance(item, ApplicationModule) and exclude_root:
                continue
            yield item

    def add_module(
        self,
        container: Container,
        module: t.Union[t.Type[StarletteAPIModuleBase], BaseModule, t.Type[T]],
        **init_kwargs: t.Any,
    ) -> t.Tuple[t.Union[StarletteAPIModuleBase, BaseModule, T], bool]:
        if isinstance(module, BaseModule) and module.get_module() in self:
            return module, False

        if module in self._data:
            return self._data.get(module), False  # type: ignore

        _module_instance = container.install(module=module, **init_kwargs)
        self._data.update(self._process_modules([_module_instance]))
        self._app_modules = []  # clear _app_modules cache
        return _module_instance, True
