import typing as t

from injector import (
    CallableProvider as CallableProvider,
)
from injector import (
    ClassProvider as ClassProvider,
)
from injector import Injector
from injector import (
    InstanceProvider as InstanceProvider,
)
from injector import (
    Provider as Provider,
)
from injector import (
    UnknownProvider as UnknownProvider,
)
from injector import (
    provider as provider_decorator,
)

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

    def get(self, injector: Injector) -> T:  # type: ignore[type-var]
        return injector.create_object(  # type:ignore[no-any-return]
            self._cls, additional_kwargs=self._init_kwargs
        )
