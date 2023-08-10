import typing as t

from ellar.common import Identity


class UserIdentity(Identity):
    roles: t.Any
    first_name: t.Optional[str]
    last_name: t.Optional[str]
    username: t.Optional[str]
    email: t.Optional[str]
