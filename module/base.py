import typing as t
import inspect
from abc import ABC, abstractmethod

from injector import Module as _InjectorModule
from starletteapi.di import ServiceConfig
from starletteapi.guard import GuardCanActivate
from starletteapi.controller import Controller
from starletteapi.templating.interface import ModuleTemplating
from starletteapi.routing import ModuleRouter
from pathlib import Path
from starletteapi.di.injector import Container

if t.TYPE_CHECKING:
    from starletteapi.main import StarletteApp

T = t.TypeVar('T')


def _configure_module(func):
    def _configure_module_wrapper(self, container: Container) -> t.Any:
        result = func(self, container=container)
        if hasattr(self, '_module_decorator'):
            _module_decorator = t.cast(Module, self._module_decorator)
            _module_decorator.configure_module(container=container)
        return result
    return _configure_module_wrapper


class StarletteAPIModuleBase(_InjectorModule):
    _module_decorator: t.Optional['Module']

    def register_services(self, container: Container) -> None:
        """Register other services manually"""

    @_configure_module
    def configure(self, container: Container) -> None:
        self.register_services(container=container)


class ApplicationModuleBase(StarletteAPIModuleBase):
    @classmethod
    @abstractmethod
    def get_on_startup(cls) -> t.List[t.Callable]:
        """run on application startup"""
        return []

    @classmethod
    @abstractmethod
    def get_on_shutdown(cls) -> t.List[t.Callable]:
        """run on application shutdown"""
        return []

    @classmethod
    @abstractmethod
    def get_lifespan(cls) -> t.Optional[t.Callable[["StarletteApp"], t.AsyncContextManager]]:
        return None

    @classmethod
    @abstractmethod
    def on_app_ready(cls, app: 'StarletteApp') -> None:
        """Execute other actions that has to do with app instance"""


class BaseModule(ModuleTemplating, ABC):
    @property
    @abstractmethod
    def module(self) -> t.Union[t.Type[StarletteAPIModuleBase], t.Type[ApplicationModuleBase]]:
        """decorated module class"""


class Module(BaseModule):
    def __init__(
            self,
            *,
            name: t.Optional[str] = __name__,
            controllers: t.Sequence[Controller] = tuple(),
            routers: t.Sequence[ModuleRouter] = tuple(),
            services: t.Sequence[t.Union[t.Type, ServiceConfig]] = tuple(),
            template_folder: t.Optional[str] = None,
            base_directory: t.Optional[str] = None,
            static_folder: str = 'static',
    ):
        self.name = name
        self.controllers = controllers
        self.services = services
        self._template_folder = template_folder
        self._static_folder = static_folder
        self._module_class: t.Optional[t.Union[t.Type[StarletteAPIModuleBase], t.Type[ApplicationModuleBase]]] = None
        self._module_base_directory = base_directory
        self.module_routers = routers

    @property
    def module(self) -> t.Union[t.Type[StarletteAPIModuleBase], t.Type[ApplicationModuleBase]]:
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
        for _provider in self.get_services():
            _provider.register(container)

        for controller in self.get_controllers():
            container.add_exact_transient(concrete_type=controller.controller_class)

    def get_controllers(self) -> t.List[Controller]:
        if hasattr(self, '_controllers'):
            return self._controllers

        if not isinstance(self.controllers, list):
            self._controllers = list(self.controllers)
        return self._controllers

    def get_services(self) -> t.List[ServiceConfig]:
        if hasattr(self, '_services'):
            return self._services

        self._services = []
        for item in self.services:
            if not isinstance(item, ServiceConfig):
                self._services.append(ServiceConfig(t.cast(t.Type[T], item)))
                continue
            self._services.append(item)
        return self._services

    def get_module_routers(self) -> t.List[ModuleRouter]:
        if not self.module_routers:
            return []

        if not isinstance(self.module_routers, list):
            self.module_routers = list(self.module_routers)
        return self.module_routers


TAppModuleKey = t.Type[t.Union[StarletteAPIModuleBase, ApplicationModuleBase]]
TAppModuleValue = t.Union[StarletteAPIModuleBase, Module]
TAppModule = t.Dict[TAppModuleKey, TAppModuleValue]


class _AppModules(t.Mapping):
    _modules: TAppModule
    _app_modules: t.List[t.Union[BaseModule, Module]]

    @classmethod
    def _process_modules(
            cls,
            modules: t.Union[t.Sequence[Module], t.Sequence[t.Type], t.Sequence[BaseModule]]
    ) -> TAppModule:
        _result: TAppModule = {}
        for module in modules:
            instance = module
            if isinstance(module, type) and issubclass(module, StarletteAPIModuleBase):
                instance = module()
                _result[module] = instance
                continue
            _result[instance.module] = instance
        return _result

    def modules(self, exclude_root: bool = False) -> t.Iterator[t.Union[BaseModule, Module]]:
        if not self._app_modules:
            for module in self._modules.values():
                if isinstance(module, BaseModule):
                    self._app_modules.append(module)

        for item in self._app_modules:
            if isinstance(item, ApplicationModule) and exclude_root:
                continue
            yield item

    def add_module(
            self,
            container: Container,
            module: t.Union[t.Type[StarletteAPIModuleBase], BaseModule, t.Type[T]]
    ) -> t.Tuple[t.Union[StarletteAPIModuleBase, BaseModule, T], bool]:
        if isinstance(module, BaseModule) and module.module in self:
            return module, False

        if module in self:
            return self.get(module), False

        _module_instance = container.install(module=module)
        self._modules.update(self._process_modules([_module_instance]))
        self._app_modules = []  # clear _app_modules cache
        return _module_instance, True

    def __getitem__(self, k: TAppModuleKey) -> TAppModuleValue:
        return self._modules.__getitem__(k)

    def __contains__(self, item: TAppModuleKey) -> bool:
        return item in self._modules

    def __len__(self) -> int:
        return len(self._modules)

    def __iter__(self) -> t.Iterator[t.Any]:
        return iter(self._modules)


class ApplicationModule(Module, _AppModules):
    def __init__(
            self,
            *,
            controllers: t.Sequence[Controller] = tuple(),
            routers: t.Sequence[ModuleRouter] = tuple(),
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
        self._modules: TAppModule = self._process_modules([self] + list(modules))
        self._app_modules = []
        self.global_guards = global_guards or []

    def __call__(self, module_class: t.Type) -> 'ApplicationModule':
        if isinstance(module_class, type) and issubclass(module_class, ApplicationModuleBase):
            self._module_class = module_class
        else:
            self._module_class = type(
                module_class.__name__, (module_class, ApplicationModuleBase), {'_module_decorator': self}
            )
        self.resolve_module_base_directory(module_class)
        return self

    def get_controllers(self) -> t.List[Controller]:
        controllers = super(ApplicationModule, self).get_controllers()
        for module in self.modules(exclude_root=True):
            controllers.extend(module.get_controllers())

        return controllers or []

    def get_module_routers(self) -> t.List[ModuleRouter]:
        module_routers = super(ApplicationModule, self).get_module_routers()
        for module in self.modules(exclude_root=True):
            module_routers.extend(module.get_module_routers())

        return module_routers or []

    def configure_module(self, container: Container) -> None:
        super().configure_module(container=container)
        for module in self.modules(exclude_root=True):
            container.install(module)
