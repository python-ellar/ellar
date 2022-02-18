import inspect
from abc import ABC, abstractmethod
from typing import List, Type, TYPE_CHECKING, Union, Sequence, Dict, AsyncContextManager, Callable, Any, Optional, cast

from injector import Module as _InjectorModule

from starletteapi.di.injector import Container
from starletteapi.di.scopes import ScopeDecorator, DIScope, SingletonScope
from starletteapi.middleware import Middleware
from starletteapi.requests import Request
from starletteapi.guard import GuardCanActivate
from starletteapi.controller import Controller
from starletteapi.types import TRequest
from starletteapi.templating.interface import ModuleTemplating
from starletteapi.routing import ModuleRouter
from pathlib import Path

if TYPE_CHECKING:
    from starletteapi.main import StarletteApp


def _configure_module(func):
    def _configure_module_wrapper(self, container: Container) -> Any:
        result = func(self, container=container)
        if hasattr(self, '_module_decorator'):
            _module_decorator = cast(Module, self._module_decorator)
            _module_decorator.configure_module(container=container)
        return result
    return _configure_module_wrapper


class StarletteAPIModuleBase(_InjectorModule):
    _module_decorator: Optional['Module']

    def configure_module(self, container: Container) -> None:
        """Register other services manually"""

    @_configure_module
    def configure(self, container: Container) -> None:
        self.configure_module(container=container)


class ApplicationModuleBase(StarletteAPIModuleBase):
    @classmethod
    @abstractmethod
    def register_custom_exceptions(
            cls, exception_handlers: Dict
    ) -> Dict[Union[int, Type[Exception]], Callable[[TRequest, Type[Exception]], Any]]:
        """

        :param exception_handlers: A dictionary mapping either integer status codes,
            or exception class types onto callables which handle the exceptions.
            Exception handler callables should be of the form
            `handler(request, exc) -> response` and may be be either standard functions, or
            async functions.
        :return: Dict
        """
        return exception_handlers

    @classmethod
    @abstractmethod
    def get_on_startup(cls) -> List[Callable]:
        """run on application startup"""
        return []

    @classmethod
    @abstractmethod
    def get_on_shutdown(cls) -> List[Callable]:
        """run on application shutdown"""
        return []

    @classmethod
    @abstractmethod
    def get_lifespan(cls) -> Optional[Callable[["StarletteApp"], AsyncContextManager]]:
        return None


class BaseModule(ModuleTemplating, ABC):
    @property
    @abstractmethod
    def module(self) -> Union[Type[StarletteAPIModuleBase], Type[ApplicationModuleBase]]:
        """decorated module class"""


class Module(BaseModule):
    def __init__(
            self,
            *,
            name: Optional[str] = __name__,
            controllers: Sequence[Controller] = tuple(),
            routers: Sequence[ModuleRouter] = tuple(),
            providers: Sequence[Type] = tuple(),
            template_folder: Optional[str] = None,
            base_directory: Optional[str] = None,
            static_folder: str = 'static',
    ):
        self.name = name
        self.controllers = controllers
        self.providers = providers
        self._template_folder = template_folder
        self._static_folder = static_folder
        self._module_class: Optional[Union[Type[StarletteAPIModuleBase], Type[ApplicationModuleBase]]] = None
        self._module_base_directory = base_directory
        self.module_routers = routers

    @property
    def module(self) -> Union[Type[StarletteAPIModuleBase], Type[ApplicationModuleBase]]:
        return self._module_class

    def __call__(self, module_class: Type) -> 'Module':
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

    def configure_module(self, container: Container) -> None:
        for _provider in self.get_providers():
            scope = cast(Union[Type[DIScope], ScopeDecorator], getattr(_provider, '__di_scope__', SingletonScope))
            container.register(base_type=_provider, scope=scope)

    def get_controllers(self) -> List[Controller]:
        if not self.controllers:
            return []

        if not isinstance(self.controllers, list):
            self.controllers = list(self.controllers)
        return self.controllers

    def get_providers(self) -> List[Type]:
        if not self.providers:
            return []

        if not isinstance(self.providers, list):
            self.providers = list(self.providers)
        return self.providers

    def get_module_routers(self) -> List[ModuleRouter]:
        if not self.module_routers:
            return []

        if not isinstance(self.module_routers, list):
            self.module_routers = list(self.module_routers)
        return self.module_routers


class ApplicationModule(Module):
    def __init__(
            self,
            *,
            controllers: Sequence[Controller] = tuple(),
            routers: Sequence[ModuleRouter] = tuple(),
            providers: Sequence[Type] = tuple(),
            middleware: Sequence[Middleware] = (),
            modules: Union[Sequence[Module], Sequence[Type]] = tuple(),
            guards: List[Union[Type[GuardCanActivate], GuardCanActivate]] = None,
            template_folder: Optional[str] = None,
            base_directory: Optional[str] = None,
            static_folder: str = 'static',
    ) -> None:
        super().__init__(
            controllers=controllers,
            providers=providers,
            template_folder=template_folder,
            base_directory=base_directory,
            static_folder=static_folder,
            routers=routers
        )
        self._modules: Union[List[Module], List[Type]] = []
        self.registered_modules = modules or ()
        self.guards: List[Union[Type[GuardCanActivate], GuardCanActivate]] = guards or []
        self.middleware: Sequence[Middleware] = middleware or ()

    def get_modules(self) -> Union[List[Module], List[Type]]:
        if self._modules:
            return self._modules

        if self.registered_modules and not isinstance(self.registered_modules, list):
            self.registered_modules = list(self.registered_modules)

        for module in self.registered_modules:
            instance = module
            if isinstance(module, type) and issubclass(module, StarletteAPIModuleBase):
                instance = module()
            self._modules.append(instance)
        return self._modules

    def __call__(self, module_class: Type) -> 'ApplicationModule':
        if isinstance(module_class, type) and issubclass(module_class, ApplicationModuleBase):
            self._module_class = module_class
        else:
            self._module_class = type(
                module_class.__name__, (module_class, ApplicationModuleBase), {'_module_decorator': self}
            )
        self.resolve_module_base_directory(module_class)
        return self

    def get_controllers(self) -> List[Controller]:
        controllers = super(ApplicationModule, self).get_controllers()
        for module in self.get_modules():
            controllers.extend(module.get_controllers())

        return controllers or []

    def get_module_routers(self) -> List[ModuleRouter]:
        module_routers = super(ApplicationModule, self).get_module_routers()
        for module in self.get_modules():
            module_routers.extend(module.get_module_routers())

        return module_routers or []

    def configure_module(self, container: Container) -> None:
        super().configure_module(container=container)
        modules = self.get_modules()
        for dec_module in modules:
            container.install(dec_module.module)

    def register_custom_exceptions(
            self, exception_handlers: Dict
    ) -> Dict[Union[int, Type[Exception]], Callable[[Request, Type[Exception]], Any]]:
        """

        :param exception_handlers: A dictionary mapping either integer status codes,
            or exception class types onto callables which handle the exceptions.
            Exception handler callables should be of the form
            `handler(request, exc) -> response` and may be be either standard functions, or
            async functions.
        :return: Dict
        """
        return self.module.register_custom_exceptions(exception_handlers)

    def get_on_startup(self) -> List[Callable]:
        """run on application startup"""
        return self.module.get_on_startup()

    def get_on_shutdown(self) -> List[Callable]:
        """run on application shutdown"""
        return self.module.get_on_shutdown()

    def get_lifespan(self) -> Optional[Callable[["StarletteApp"], AsyncContextManager]]:
        return self.module.get_lifespan()
