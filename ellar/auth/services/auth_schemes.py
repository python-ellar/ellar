import typing as t

from ellar.common import IIdentitySchemes

from ..handlers import AuthenticationHandlerType


class AppIdentitySchemes(IIdentitySchemes):
    """
    Manages the collection of registered authentication schemes for the application.
    """

    __slots__ = ("_authentication_schemes",)

    def __init__(self) -> None:
        self._authentication_schemes: t.Dict[str, AuthenticationHandlerType] = {}

    def add_authentication(
        self, authentication_scheme: AuthenticationHandlerType
    ) -> None:
        """
        Registers a new authentication scheme.
        """
        self._authentication_schemes[authentication_scheme.scheme] = (
            authentication_scheme
        )

    def find_authentication_scheme(self, scheme: str) -> AuthenticationHandlerType:
        """
        Retrieves an authentication scheme by name.

        :raises RuntimeError: If the scheme is not found.
        """
        try:
            return self._authentication_schemes[scheme]
        except KeyError as ex:
            raise RuntimeError(
                f'No Authentication Scheme found with the name:"{scheme}"'
            ) from ex

    def get_authentication_schemes(
        self,
    ) -> t.Generator[AuthenticationHandlerType, t.Any, t.Any]:
        """
        Yields all registered authentication schemes.
        """
        for _, v in self._authentication_schemes.items():
            yield v
