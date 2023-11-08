import typing as t
from abc import ABC, abstractmethod

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.auth.handlers import AuthenticationHandlerType


class IIdentitySchemes(ABC):
    @abstractmethod
    def add_authentication(self, authentication: "AuthenticationHandlerType") -> None:
        """Add Authentication Handler"""

    @abstractmethod
    def find_authentication_scheme(self, scheme: str) -> "AuthenticationHandlerType":
        """Finds Authentication Scheme"""

    @abstractmethod
    def get_authentication_schemes(
        self,
    ) -> t.Generator["AuthenticationHandlerType", t.Any, t.Any]:
        """Gets all the registered Authentication Handlers"""
