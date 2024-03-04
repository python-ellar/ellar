import typing as t

from ellar.common import IIdentitySchemes

from ..handlers import AuthenticationHandlerType


class AppIdentitySchemes(IIdentitySchemes):
    __slots__ = ("_authentication_schemes",)

    def __init__(self) -> None:
        self._authentication_schemes: t.Dict[str, AuthenticationHandlerType] = {}

    def add_authentication(
        self, authentication_scheme: AuthenticationHandlerType
    ) -> None:
        self._authentication_schemes[authentication_scheme.scheme] = (
            authentication_scheme
        )

    def find_authentication_scheme(self, scheme: str) -> AuthenticationHandlerType:
        try:
            return self._authentication_schemes[scheme]
        except KeyError as ex:
            raise RuntimeError(
                f'No Authentication Scheme found with the name:"{scheme}"'
            ) from ex

    def get_authentication_schemes(
        self,
    ) -> t.Generator[AuthenticationHandlerType, t.Any, t.Any]:
        for _, v in self._authentication_schemes.items():
            yield v
