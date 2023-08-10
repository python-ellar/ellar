import typing as t

from ellar.common.compatible import AttributeDict


class Identity(AttributeDict):
    """Represent the user's identity."""

    auth_type: t.Optional[str]
    issuer: t.Optional[str]

    def __init__(self, auth_type: t.Optional[str] = None, **kwargs: t.Any) -> None:
        kwargs.setdefault("id", kwargs.get("id", kwargs.get("sub")))
        kwargs.update({"auth_type": auth_type})
        super().__init__(**kwargs)

    @property
    def is_authenticated(self) -> bool:
        return bool(self.id)

    def __repr__(self) -> str:  # pragma: no cover
        return '<{0} id="{1}" auth_type="{2}" is_authenticated={3}>'.format(
            self.__class__.__name__, self.id, self.auth_type, self.is_authenticated
        )


class AnonymousIdentity(Identity):
    def __init__(self) -> None:
        super().__init__(id=None)
