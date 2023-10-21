import typing as t
from abc import ABC, abstractmethod

from ellar.common.types import TScope


class IAPIVersioningResolver(ABC):
    @abstractmethod
    def can_activate(self, route_versions: t.Set[t.Union[int, float, str]]) -> bool:
        """Validate Version routes"""


class IAPIVersioning(ABC):
    @abstractmethod
    def get_version_resolver(self, scope: TScope) -> IAPIVersioningResolver:
        """Retrieve Version Resolver"""

    @classmethod
    def __get_validators__(
        cls: t.Type["IAPIVersioning"],
    ) -> t.Iterable[t.Callable[..., t.Any]]:
        # for Pydantic Model Validation
        yield cls.__validate

    @classmethod
    def __validate(cls, v: t.Any) -> t.Any:
        if not isinstance(v, cls):
            raise ValueError(f"Expected BaseAPIVersioning, received: {type(v)}")
        return v
