import typing as t

from injector import Binder, Module as _InjectorModule

from ellar.constants import MODULE_FIELDS
from ellar.core.conf import Config
from ellar.core.modules.builder import ModuleBaseBuilder
from ellar.di.injector import Container

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core import App


class ModuleBaseMeta(type):
    __MODULE_FIELDS__: t.Dict = {}

    @t.no_type_check
    def __init__(cls, name, bases, namespace) -> None:
        super().__init__(name, bases, namespace)
        cls.__MODULE_FIELDS__: t.Dict = {}

        for base in reversed(bases):
            ModuleBaseBuilder(cls).build(getattr(base, MODULE_FIELDS, dict()))
        ModuleBaseBuilder(cls).build(namespace)


class ModuleBase(_InjectorModule, metaclass=ModuleBaseMeta):
    @classmethod
    def before_init(cls, config: Config) -> None:
        """Before Module initialisation"""

    def application_ready(self, app: "App") -> None:
        """Application Ready"""

    def register_services(self, container: Container) -> None:
        """Register other services manually"""

    def configure(self, container: Binder) -> None:
        """Injector Module Support. Override register_services instead"""
        self.register_services(t.cast(Container, container))
