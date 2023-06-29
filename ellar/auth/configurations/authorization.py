import typing as t

from ..interfaces import IAuthorizationConfig
from ..policy import Policy


class AuthorizationConfig(IAuthorizationConfig):
    __slots__ = ("_policies",)

    def __init__(self) -> None:
        self._policies: t.Dict[str, Policy] = {}

    def add_authorization(self, name: str, policy: Policy) -> None:
        self._policies[name] = policy

    def find_policy(self, name: str) -> Policy:
        try:
            return self._policies[name]
        except KeyError:
            raise RuntimeError(f'No policy found with the name:"{name}"')
