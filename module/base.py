import typing as t
import inspect
from abc import ABC, abstractmethod, ABCMeta

from injector import Module as _InjectorModule
from starlette.routing import BaseRoute

from starletteapi.types import T
from starletteapi.compatible import DataMapper
from starletteapi.di import ServiceConfig
from starletteapi.guard import GuardCanActivate
from starletteapi.controller import ControllerBase, ControllerType
from starletteapi.templating.interface import ModuleTemplating
from starletteapi.routing import ModuleRouter, RouteDefinitions
from pathlib import Path
from starletteapi.di.injector import Container
from .events import ModuleEvent, ApplicationEvent


def _configure_module(func):
    def _configure_module_wrapper(self, container: Container) -> t.Any:
        result = func(self, container=container)
        if hasattr(self, '_module_decorator'):
            _module_decorator = t.cast(Module, self._module_decorator)
            _module_decorator.configure_module(container=container)
        return result

    return _configure_module_wrapper


class StarletteAPIModuleBaseMeta(ABCMeta):
    @t.no_type_check
    def __new__(mcls, name, bases, namespace, **kwargs):
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)  # type: ignore
        cls._module_decorator = namespace.get('_module_decorator', None)
        return cls


class StarletteAPIModuleBase(_InjectorModule, metaclass=StarletteAPIModuleBaseMeta):
    _module_decorator: t.Optional['Module']

    def register_services(self, container: Container) -> None:
        """Register other services manually"""

    @_configure_module
    def configure(self, container: Container) -> None:
        self.register_services(container=container)


class BaseModule(ModuleTemplating, ABC, metaclass=ABCMeta):
    on_startup: ModuleEvent
    on_shutdown: ModuleEvent
    before_initialisation: ApplicationEvent
    after_initialisation: ApplicationEvent

    def __init__(self):
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
            controllers: t.Sequence[t.Type[ControllerBase]] = tuple(),
            routers: t.Sequence[t.Union[ModuleRouter, RouteDefinitions]] = tuple(),
            services: t.Sequence[t.Union[t.Type, ServiceConfig]] = tuple(),
            template_folder: t.Optional[str] = None,
            base_directory: t.Optional[str] = None,
            static_folder: str = 'static',
    ):
        super(Module, self).__init__()
        self.name = name
        self._controllers = [] if controllers is None else list(controllers)
        self._services: t.List[ServiceConfig] = []
        self._template_folder = template_folder
        self._static_folder = static_folder
        self._module_class: t.Optional[t.Type[StarletteAPIModuleBase]] = None
        self._module_base_directory = base_directory
        self._module_routers = self._get_module_routers(routers=routers)
        self._builder_service(services=services)
        self.on_startup = ModuleEvent()
        self.on_shutdown = ModuleEvent()
        self.before_initialisation = ApplicationEvent()
        self.after_initialisation = ApplicationEvent()

    def get_module(self) -> t.Type[StarletteAPIModuleBase]:
        return self._module_class

    def __call__(self, module_class: t.Type) -> 'Module':
        if isinstance(module_class, type) and issubclass(module_class, StarletteAPIModuleBase):
            self._module_class = module_class
        else:
            self._module_class = type(
                module_class.__name__, (module_class, StarletteAPIModuleBase), {'_module_decorator': self}
            )
        self.resolve_module_base_directory(module_class)
        return self

    def resolve_module_base_directory(self, module_class):
        if not self._module_base_directory:
            self._module_base_directory = Path(inspect.getfile(module_class)).resolve().parent
        module_class._module_decorator = self

    def configure_module(self, container: Container) -> None:
        for _provider in self._services:
            _provider.register(container)

        for controller in self._controllers:
            container.add_exact_scoped(concrete_type=controller)

    def _builder_service(self, services: t.Sequence[t.Union[t.Type, ServiceConfig]]):
        for item in services:
            if not isinstance(item, ServiceConfig):
                self._services.append(ServiceConfig(t.cast(t.Type[T], item)))
                continue
            self._services.append(item)

    def _build_routes(self) -> t.List[BaseRoute]:
        routes = list(self._module_routers)
        for controller in self._controllers:
            if type(controller) == ControllerType:
                routes.append(controller.get_route())
        return routes

    @classmethod
    def _get_module_routers(cls, routers: t.Sequence[t.Union[ModuleRouter, RouteDefinitions]]) -> t.List[BaseRoute]:
        results = []
        for item in routers:
            if isinstance(item, RouteDefinitions):
                results.extend(item.routes)
                continue
            if isinstance(item, ModuleRouter):
                item.build_routes()
            results.append(item)
        return results


TAppModuleValue = t.Union[StarletteAPIModuleBase, Module]
TAppModule = t.Dict[t.Type[StarletteAPIModuleBase], TAppModuleValue]


class _AppModules(DataMapper[t.Type[StarletteAPIModuleBase], TAppModuleValue]):
    _data: TAppModule
    _app_modules: t.List[t.Union[BaseModule, Module]]

    @classmethod
    def _process_modules(
            cls,
            modules: t.Union[t.Sequence[Module], t.Sequence[t.Type], t.Sequence[BaseModule]]
    ) -> TAppModule:
        _result: TAppModule = {}
        for module in modules:
            instance = module
            if isinstance(module, StarletteAPIModuleBase):
                instance = module._module_decorator
                _result[instance.get_module()] = instance
                continue

            if isinstance(module, type) and issubclass(module, StarletteAPIModuleBase):
                instance = module()
                _result[module] = instance
                continue

            if hasattr(instance, 'get_module'):
                _result[instance.get_module()] = instance

        return _result

    def modules(self, exclude_root: bool = False) -> t.Iterator[t.Union[BaseModule, Module]]:
        if not self._app_modules:
            for module in self.values():
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
            **init_kwargs: t.Any
    ) -> t.Tuple[t.Union[StarletteAPIModuleBase, BaseModule, T], bool]:
        if isinstance(module, BaseModule) and module.get_module() in self:
            return module, False

        if module in self:
            return self.get(module), False

        _module_instance = container.install(module=module, **init_kwargs)
        self._data.update(self._process_modules([_module_instance]))
        self._app_modules = []  # clear _app_modules cache
        return _module_instance, True


class ApplicationModule(Module, _AppModules):
    def __init__(
            self,
            *,
            controllers: t.Sequence[t.Type[ControllerBase]] = tuple(),
            routers: t.Sequence[t.Union[ModuleRouter, RouteDefinitions]] = tuple(),
            services: t.Sequence[t.Union[t.Type, ServiceConfig]] = tuple(),
            modules: t.Union[t.Sequence[Module], t.Sequence[t.Type], t.Sequence[BaseModule]] = tuple(),
            global_guards: t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]] = None,
            template_folder: t.Optional[str] = None,
            base_directory: t.Optional[str] = None,
            static_folder: str = 'static',
    ) -> None:
        super().__init__(
            controllers=controllers,
            services=services,
            template_folder=template_folder,
            base_directory=base_directory,
            static_folder=static_folder,
            routers=routers
        )
        self._data: TAppModule = self._process_modules(modules)
        self._app_modules = []
        self._global_guards = global_guards or []

    @property
    def global_guards(self) -> t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]]:
        return self._global_guards

    def __call__(self, module_class: t.Type) -> 'ApplicationModule':
        super().__call__(module_class)
        self._data.update(self._process_modules([self]))
        return self

    def configure_module(self, container: Container) -> None:
        super().configure_module(container=container)
        for module in self.modules(exclude_root=True):
            container.install(module)

    def _build_routes(self) -> t.List[BaseRoute]:
        routes = super()._build_routes()
        for module in self.modules(exclude_root=True):
            routes.extend(module._build_routes())
        return routes

    def get_startup_events(self) -> t.List[t.Callable]:
        events = list(self.on_startup)
        for module in self.modules(exclude_root=True):
            events.extend(module.on_startup)
        return events

    def get_shutdown_events(self) -> t.List[t.Callable]:
        events = list(self.on_shutdown)
        for module in self.modules(exclude_root=True):
            events.extend(module.on_shutdown)
        return events

    def get_before_events(self) -> t.List[t.Callable]:
        events = list(self.before_initialisation)
        for module in self.modules(exclude_root=True):
            events.extend(module.before_initialisation)
        return events

    def get_after_events(self) -> t.List[t.Callable]:
        events = list(self.after_initialisation)
        for module in self.modules(exclude_root=True):
            events.extend(module.after_initialisation)
        return events
