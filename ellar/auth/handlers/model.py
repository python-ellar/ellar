import typing as t
from abc import ABC, abstractmethod

from ellar.common import Identity, IHostContext


class BaseAuthenticationHandler(ABC):
    """
    Base class for all authentication handlers.

    To create a custom authentication scheme, inherit from this class and implement the `authenticate` method.
    You must also define a `scheme` attribute (e.g., 'bearer', 'basic', 'api-key').
    """

    scheme: str

    def __init_subclass__(cls, **kwargs: str) -> None:
        if not hasattr(cls, "scheme"):
            raise RuntimeError(f"'{cls.__name__}' has no attribute 'scheme'")

    @classmethod
    def openapi_security_scheme(cls) -> t.Optional[t.Dict]:
        return None

    @abstractmethod
    async def authenticate(self, context: IHostContext) -> t.Optional[Identity]:
        """
        authenticate the request and return an Identity or None
        """


AuthenticationHandlerType = t.Union[
    BaseAuthenticationHandler, t.Type[BaseAuthenticationHandler]
]
