import typing as t
from abc import ABC, abstractmethod

from ellar.common.types import TScope
from ellar.pydantic import as_pydantic_validator


class IAPIVersioningResolver(ABC):
    @abstractmethod
    def can_activate(self, route_versions: t.Set[t.Union[int, float, str]]) -> bool:
        """Validate Version routes"""


@as_pydantic_validator("__validate_input__", schema={"type": "object"})
class IAPIVersioning(ABC):
    @abstractmethod
    def get_version_resolver(self, scope: TScope) -> IAPIVersioningResolver:
        """Retrieve Version Resolver"""

    @classmethod
    def __validate_input__(cls, v: t.Any, _: t.Any) -> t.Any:
        if not isinstance(v, cls):
            raise ValueError(f"Expected BaseAPIVersioning, received: {type(v)}")
        return v
