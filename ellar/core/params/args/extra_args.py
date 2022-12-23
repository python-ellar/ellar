import inspect
import typing as t

from ellar.types import T


class ExtraEndpointArg(t.Generic[T]):
    __slots__ = ("name", "annotation", "default")

    empty = inspect.Parameter.empty

    def __init__(
        self, *, name: str, annotation: t.Type[T], default_value: t.Any = None
    ):
        self.name = name
        self.annotation = annotation
        self.default = default_value or self.empty

    def resolve(self, kwargs: t.Dict) -> T:
        if self.name in kwargs:
            return t.cast(T, kwargs.pop(self.name))
        raise AttributeError(f"{self.name} ExtraOperationArg not found")
