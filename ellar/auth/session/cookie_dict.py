import typing as t
from functools import wraps


@t.no_type_check
def _on_update_callback(
    cls: t.Type["SessionCookieObject"],
) -> t.Type["SessionCookieObject"]:
    def _decor(func):
        @wraps(func)
        def _wrap(self: "SessionCookieObject", *args, **kwargs) -> t.Any:
            self.modified = True
            self.accessed = True
            return func(self, *args, **kwargs)

        return _wrap

    cls.__setitem__ = _decor(cls.__setitem__)
    cls.__delitem__ = _decor(cls.__delitem__)

    cls.clear = _decor(cls.clear)
    cls.popitem = _decor(cls.popitem)

    cls.update = _decor(cls.update)
    cls.pop = _decor(cls.pop)

    cls.setdefault = _decor(cls.setdefault)

    return cls


@_on_update_callback
class SessionCookieObject(dict):
    __slots__ = ("modified", "accessed")

    def __init__(self, *__n: t.Any, **__m: t.Any) -> None:
        super().__init__(*__n, **__m)
        self.modified: bool = False
        self.accessed: bool = False

    def __getattribute__(self, name: t.Any) -> t.Optional[t.Any]:
        if name in self:
            return self[name]
        try:
            return super(SessionCookieObject, self).__getattribute__(name)
        except Exception:
            return None

    def __setattr__(self, key: t.Any, value: t.Any) -> None:
        if key in self.__slots__:
            super(SessionCookieObject, self).__setattr__(key, value)
            return

        self[key] = value

    def __getitem__(self, key: str) -> t.Any:
        self.accessed = True
        return super().__getitem__(key)

    def get(self, key: str, default: t.Any = None) -> t.Any:
        self.accessed = True
        return super().get(key, default)
