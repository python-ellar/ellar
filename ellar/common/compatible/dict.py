import typing as t

from ..types import KT, VT


class AttributeDictAccessMixin:
    def __getattribute__(self, name: t.Any) -> t.Optional[t.Any]:
        if name in self:
            return self[name]
        try:
            return super(AttributeDictAccessMixin, self).__getattribute__(name)
        except Exception:
            return self.__missing__(name)

    def __missing__(self, name) -> VT:
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )


class AttributeDict(AttributeDictAccessMixin, t.Dict[KT, VT]):
    def __setattr__(self, name: KT, value: VT) -> None:  # type: ignore
        self.update({name: value})

    def set_defaults(self, **kwargs: t.Any) -> None:
        for k, v in kwargs.items():
            self.setdefault(k, v)  # type: ignore

    def __missing__(self, name) -> VT:
        return None
