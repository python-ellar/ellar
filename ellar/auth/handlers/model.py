import typing as t
from abc import ABC, abstractmethod

from ellar.common import Identity, IHostContext


class BaseAuthenticationHandler(ABC):
    scheme: str

    def __init_subclass__(cls, **kwargs: str) -> None:
        if not cls.scheme:
            raise Exception("Authentication Scheme is required")

    @classmethod
    def openapi_security_scheme(cls) -> t.Optional[t.Dict]:
        return None

    @abstractmethod
    async def authenticate(self, context: IHostContext) -> t.Optional[Identity]:
        ...


AuthenticationHandlerType = t.Union[
    BaseAuthenticationHandler, t.Type[BaseAuthenticationHandler]
]
