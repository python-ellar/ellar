import typing as t

from ellar.constants import NOT_SET
from ellar.types import T

try:
    from functools import cached_property
except (Exception,):  # pragma: no cover

    class _CachedProperty(property, t.Generic[T]):
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

    cached_property = _CachedProperty
