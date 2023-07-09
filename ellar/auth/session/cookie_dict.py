import typing as t
from functools import partial

from ellar.common.compatible import AttributeDict


@t.no_type_check
def _on_update_callback(
    cls: t.Type["SessionCookieObject"],
) -> t.Type["SessionCookieObject"]:
    def _wrap(func: t.Callable, self: "SessionCookieObject", *args, **kwargs) -> t.Any:
        self.modified = True
        self.accessed = True
        return func(self, *args, **kwargs)

    cls.__setitem__ = partial(_wrap, cls.__setitem__)

    cls.__delitem__ = partial(_wrap, cls.__delitem__)
    cls.clear = partial(_wrap, cls.clear)

    cls.popitem = partial(_wrap, cls.popitem)
    cls.update = partial(_wrap, cls.update)

    cls.pop = partial(_wrap, cls.pop)
    cls.setdefault = partial(_wrap, cls.setdefault)

    return cls


@_on_update_callback
class SessionCookieObject(AttributeDict):
    modified = False
    accessed = False

    def __getitem__(self, key: str) -> t.Any:
        self.accessed = True
        return super().__getitem__(key)

    def get(self, key: str, default: t.Any = None) -> t.Any:
        self.accessed = True
        return super().get(key, default)
