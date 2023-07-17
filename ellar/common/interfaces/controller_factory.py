import typing as t
from abc import ABC, abstractmethod

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common.routing import ModuleMount


class IControllerBuildFactory(ABC):
    @abstractmethod
    def build(self, controller_type: t.Type) -> "ModuleMount":
        """Build Action"""
