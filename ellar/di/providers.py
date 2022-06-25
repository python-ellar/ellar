import typing as t

from injector import (
    CallableProvider as CallableProvider,
    ClassProvider as ClassProvider,
    InstanceProvider as InstanceProvider,
    Provider as Provider,
    UnknownProvider as UnknownProvider,
    provider as provider_decorator,
)

if t.TYPE_CHECKING:  # pragma: no cover
    from injector import Injector

T = t.TypeVar("T")

__all__ = [
    "CallableProvider",
    "ClassProvider",
    "InstanceProvider",
    "UnknownProvider",
    "Provider",
    "provider_decorator",
    "ModuleProvider",
]


class ModuleProvider(ClassProvider):
    def __init__(self, cls: t.Type[T], **init_kwargs: t.Any) -> None:
        super().__init__(cls)
        self._init_kwargs = init_kwargs

    def get(self, injector: "Injector") -> T:
        return injector.create_object(self._cls, additional_kwargs=self._init_kwargs)
