import typing as t

from ellar.common import Identity


class UserIdentity(Identity):
    @property
    def roles(self) -> t.Any:
        return self.get("roles", [])

    @property
    def first_name(self) -> t.Any:
        return self.get("first_name")

    @property
    def last_name(self) -> t.Any:
        return self.get("last_name")

    @property
    def username(self) -> t.Any:
        return self.get("username")

    @property
    def email(self) -> t.Any:
        return self.get("email")
