import typing as t
from abc import ABC, ABCMeta, abstractmethod

from injector import Module as _InjectorModule
from starlette.routing import BaseRoute

from architek.core.events import ApplicationEventManager, RouterEventManager
from architek.core.templating.interface import ModuleTemplating
from architek.di.injector import Container


class BaseModuleDecorator(ModuleTemplating, ABC, metaclass=ABCMeta):
    on_startup: RouterEventManager
    on_shutdown: RouterEventManager
    before_initialisation: ApplicationEventManager
    after_initialisation: ApplicationEventManager

    def __init__(self) -> None:
        self._routes: t.List[BaseRoute] = []

    @abstractmethod
    def get_module(self) -> t.Type["ModuleBase"]:
        """decorated module class"""

    @abstractmethod
    def configure_module(self, container: Container) -> None:
        ...

    def get_routes(self, force_build: bool = False) -> t.List[BaseRoute]:
        if not force_build and self._routes:
            return self._routes
        self._routes = self._build_routes()
        return self._routes

    @abstractmethod
    def _build_routes(self) -> t.List[BaseRoute]:
        """build module controller routes"""


def _configure_module(func: t.Callable) -> t.Any:
    def _configure_module_wrapper(self: t.Any, container: Container) -> t.Any:
        _module_decorator = getattr(self, "_module_decorator", None)
        if _module_decorator:
            _module_decorator = t.cast(BaseModuleDecorator, self._module_decorator)
            _module_decorator.configure_module(container=container)
        result = func(self, container=container)
        return result

    return _configure_module_wrapper


class ModuleBaseMeta(ABCMeta):
    _module_decorator: t.Optional[BaseModuleDecorator]

    @t.no_type_check
    def __new__(mcls, name, bases, namespace, **kwargs):
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)
        cls._module_decorator = namespace.get("_module_decorator", None)
        return cls

    def get_module_decorator(cls) -> t.Optional["BaseModuleDecorator"]:
        return cls._module_decorator


class ModuleBase(_InjectorModule, metaclass=ModuleBaseMeta):
    def register_services(self, container: Container) -> None:
        """Register other services manually"""

    @_configure_module
    def configure(self, container: Container) -> None:
        self.register_services(container=container)
