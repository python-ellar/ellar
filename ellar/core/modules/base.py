import typing as t

from injector import Module as _InjectorModule

from ellar.core.conf import Config
from ellar.core.modules.builder import ModuleBaseBuilder
from ellar.di.injector import Container

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core import App


class ModuleBaseMeta(type):
    @t.no_type_check
    def __init__(cls, name, bases, namespace) -> None:
        super().__init__(name, bases, namespace)
        ModuleBaseBuilder(cls).build(namespace)


class ModuleBase(_InjectorModule, metaclass=ModuleBaseMeta):
    @classmethod
    def before_init(cls, config: Config) -> None:
        """Before Module initialisation"""

    def application_ready(self, app: "App") -> None:
        """Application Ready"""

    def register_services(self, container: Container) -> None:
        """Register other services manually"""

    def configure(self, container: Container) -> None:
        """Override register_services"""
        self.register_services(container=container)
