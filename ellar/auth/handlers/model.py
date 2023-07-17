import typing as t
from abc import ABC, abstractmethod

from ellar.common import Identity, IHostContext


class BaseAuthenticationHandler(ABC):
    scheme: str

    def __init_subclass__(cls, **kwargs: str) -> None:
        if not hasattr(cls, "scheme"):
            raise RuntimeError(f"'{cls.__name__}' has no attribute 'scheme'")

    @classmethod
    def openapi_security_scheme(cls) -> t.Optional[t.Dict]:
        return None

    @abstractmethod
    async def authenticate(self, context: IHostContext) -> t.Optional[Identity]:
        """Authenticate Action goes here"""


AuthenticationHandlerType = t.Union[
    BaseAuthenticationHandler, t.Type[BaseAuthenticationHandler]
]
