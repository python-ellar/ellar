import typing as t
from abc import ABC, abstractmethod

if t.TYPE_CHECKING:  # pragma: no cover
    from .handlers import AuthenticationHandlerType


class IAuthConfig(ABC):
    @abstractmethod
    def add_authentication(self, authentication: "AuthenticationHandlerType") -> None:
        ...

    @abstractmethod
    def find_authentication_scheme(self, scheme: str) -> "AuthenticationHandlerType":
        ...

    @abstractmethod
    def get_authentication_schemes(
        self,
    ) -> t.Generator["AuthenticationHandlerType", t.Any, t.Any]:
        ...


class IIdentitySchemeProvider(ABC):
    @abstractmethod
    def add_authentication(self, authentication: "AuthenticationHandlerType") -> None:
        ...

    @abstractmethod
    def configure(self) -> None:
        ...
