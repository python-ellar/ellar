import typing as t
from abc import ABC, abstractmethod

from ellar.common.types import TScope


class IAPIVersioningResolver(ABC):
    @abstractmethod
    def can_activate(self, route_versions: t.Set[t.Union[int, float, str]]) -> bool:
        pass


class IAPIVersioning(ABC):
    @abstractmethod
    def get_version_resolver(self, scope: TScope) -> IAPIVersioningResolver:
        ...
