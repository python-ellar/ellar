import typing as t
from abc import ABC, abstractmethod

from starlette.routing import BaseRoute

from ellar.core.routing import ModuleRouterBase
from ellar.core.templating.interface import ModuleTemplating
from ellar.di.injector import Container

from ..base import ModuleBase


class BaseModuleDecorator(ModuleTemplating, ABC):
    template_filter: t.Callable[[str], t.Any]
    template_global: t.Callable[[str], t.Any]

    @abstractmethod
    def get_module(self) -> t.Type["ModuleBase"]:
        """decorated module class"""

    @abstractmethod
    def configure_module(self, container: Container) -> None:
        """Configures Modules Decorator During Module Base Container installation"""

    @abstractmethod
    def validate_module_decorator(self) -> None:
        """Runs module decorator validations"""

    @abstractmethod
    def get_routes(self, force_build: bool = False) -> t.List[BaseRoute]:
        """Runs flattened routes from registered controllers and routers"""

    @abstractmethod
    def get_module_routers(self) -> t.List[ModuleRouterBase]:
        """gets all ModuleRouterBase from registered controllers and routers"""
