import inspect
import re
import typing as t

from starletteapi.constants import NOT_SET

T = t.TypeVar("T")


def generate_operation_unique_id(*, name: str, path: str, method: str) -> str:
    operation_id = name + path
    operation_id = re.sub("[^0-9a-zA-Z_]", "_", operation_id)
    operation_id = operation_id + "_" + method.lower()
    return operation_id


def get_name(endpoint: t.Callable) -> str:
    if inspect.isfunction(endpoint) or inspect.isclass(endpoint):
        return endpoint.__name__
    return endpoint.__class__.__name__


class cached_property(property, t.Generic[T]):
    """A :func:`property` that is only evaluated once. Subsequent access
    returns the cached value. Setting the property sets the cached
    value. Deleting the property clears the cached value, accessing it
    again will evaluate it again.

    .. code-block:: python

        class Example:
            @cached_property
            def value(self):
                # calculate something important here
                return 42

        e = Example()
        e.value  # evaluates
        e.value  # uses cache
        e.value = 16  # sets cache
        del e.value  # clears cache

    The class must have a ``__dict__`` for this to work.

    .. versionchanged:: 2.0
        ``del obj.name`` clears the cached value.
    """

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
