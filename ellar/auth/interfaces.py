import typing as t
from abc import ABC, abstractmethod

from ellar.common import IExecutionContext

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.auth.models import AuthenticationHandlerType
    from ellar.auth.policy import Policy


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


class IAuthorizationConfig(ABC):
    @abstractmethod
    def add_authorization(self, name: str, policy: "Policy") -> None:
        ...

    @abstractmethod
    def find_policy(self, name: str) -> "Policy":
        ...


class IAuthorizationRequirement(ABC):
    @abstractmethod
    async def handle(self, context: IExecutionContext) -> bool:
        pass


class IIdentityProvider(ABC):
    @abstractmethod
    def add_authentication(self, authentication: "AuthenticationHandlerType") -> None:
        ...

    @abstractmethod
    def add_authorization(self, name: str, policy: "Policy") -> None:
        ...

    @abstractmethod
    async def configure(self) -> None:
        ...
