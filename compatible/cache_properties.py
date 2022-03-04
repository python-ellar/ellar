import typing as t
from threading import RLock
from starletteapi.constants import NOT_SET

try:
    from functools import cached_property
except:
    T = t.TypeVar('T')

    class cached_property(property, t.Generic[T]):
        def __init__(
                self,
                fget: t.Callable[[t.Any], T],
                name: t.Optional[str] = None,
                doc: t.Optional[str] = None,
        ) -> None:
            super().__init__(fget, doc=doc)
            self.__name__ = name or fget.__name__
            self.__module__ = fget.__module__

        def __set__(self, obj: object, value: T) -> None:
            obj.__dict__[self.__name__] = value

        def __get__(self, obj: object, type: type = None) -> T:  # type: ignore
            if obj is None:
                return self  # type: ignore

            value: T = obj.__dict__.get(self.__name__, NOT_SET)

            if value is NOT_SET:
                value = self.fget(obj)  # type: ignore
                obj.__dict__[self.__name__] = value

            return value

        def __delete__(self, obj: object) -> None:
            del obj.__dict__[self.__name__]


class locked_cached_property(cached_property):
    """A :func:`property` that is only evaluated once. Like
    :class:`werkzeug.utils.cached_property` except access uses a lock
    for thread safety.
    """

    def __init__(
        self,
        fget: t.Callable[[t.Any], t.Any],
        name: t.Optional[str] = None,
        doc: t.Optional[str] = None,
    ) -> None:
        super().__init__(fget, name=name, doc=doc)
        self.lock = RLock()

    def __get__(self, obj: object, type: type = None) -> t.Any:  # type: ignore
        if obj is None:
            return self

        with self.lock:
            return super().__get__(obj, type=type)

    def __set__(self, obj: object, value: t.Any) -> None:
        with self.lock:
            super().__set__(obj, value)

    def __delete__(self, obj: object) -> None:
        with self.lock:
            super().__delete__(obj)
