from __future__ import annotations

import sys
import typing as t
from functools import cached_property

from ellar.di.constants import MODULE_REF_TYPES, Tag, request_context_var
from ellar.di.injector.tree_manager import ModuleTreeManager
from ellar.di.logger import log
from ellar.di.providers import InstanceProvider, Provider
from ellar.di.types import T
from injector import Injector, Scope, ScopeDecorator
from typing_extensions import Annotated

from .container import Container
from .tag_registry import TagRegistry

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.modules import (
        ModuleBase,
        ModuleForwardRef,
        ModuleRefBase,
        ModuleSetup,
    )


def register_request_scope_context(interface: t.Type[T], value: T) -> None:
    # Sets RequestScope contexts so that they can be available when needed

    scoped_context = request_context_var.get()
    if scoped_context is None:
        return

    if isinstance(value, Provider):
        scoped_context.context.update({interface: value})
    else:
        scoped_context.context.update({interface: InstanceProvider(value)})


class _TagInfo(t.NamedTuple):
    supertype: t.Type
    tag: str


def _tag_info_interface(type_: t.Any) -> t.Optional[_TagInfo]:
    if (
        sys.version_info < (3, 10)
        and getattr(type_, "__qualname__", "") == "NewType.<locals>.new_type"
        or sys.version_info >= (3, 10)
        and type(type_).__module__ == "typing"
        and type(type_).__name__ == "NewType"
    ):
        return _TagInfo(supertype=type_.__supertype__, tag=type_.__name__)

    if isinstance(type_, (str, Tag)):
        return _TagInfo(supertype=Tag, tag=str(type_))

    return None


class EllarInjector(Injector):
    __slots__ = (
        "_stack",
        "parent",
        "container",
        "owner",
    )

    # Global tag registry shared across all injector instances
    tag_registry: t.ClassVar[TagRegistry] = TagRegistry()

    def __init__(
        self,
        auto_bind: bool = True,
        parent: t.Optional["Injector"] = None,
        owner: t.Optional["ModuleRefBase"] = None,
    ) -> None:
        self._stack = ()
        self.parent = parent
        # Binder
        self.container = self.binder = Container(
            self,
            auto_bind=auto_bind,
            parent=parent.binder if parent is not None else None,
        )
        self.owner = owner
        # Bind some useful types
        self.container.register(EllarInjector, self)
        self.container.register(Container, self.binder)

    @cached_property
    def tree_manager(self) -> ModuleTreeManager:
        return t.cast(ModuleTreeManager, self.get(ModuleTreeManager))

    @property  # type: ignore
    def binder(self) -> Container:
        return self.container

    @binder.setter
    def binder(self, value: t.Any) -> None:
        """Nothing happens"""

    def get_module(self, module: t.Type) -> t.Optional["ModuleRefBase"]:
        node = self.tree_manager.get_module(module)
        if node:
            return t.cast("ModuleRefBase", node.value)
        return None

    def get_templating_modules(
        self,
    ) -> dict[
        type[ModuleBase] | type, ModuleRefBase | "ModuleSetup" | ModuleForwardRef
    ]:
        return {
            item.value.module: item.value
            for item in self.tree_manager.get_by_ref_type(MODULE_REF_TYPES.TEMPLATE)
        }

    @t.no_type_check
    def get(
        self,
        interface: t.Union[Annotated[t.Type[T], type], Annotated[str, type], t.Any],
        scope: t.Union[ScopeDecorator, t.Type[Scope]] = None,
    ) -> T:
        data = _tag_info_interface(interface)
        if data and data.supertype is Tag:
            interface = self.tag_registry.get_interface(data.tag)

        binding, binder = self.container.get_binding(interface)
        scope = binding.scope

        if isinstance(scope, ScopeDecorator):  # pragma: no cover
            scope = scope.scope
        # Fetch the corresponding Scope instance from the Container.
        scope_binding, _ = binder.get_binding(scope)
        scope_instance = t.cast(Scope, scope_binding.provider.get(self))

        log.debug(
            f"{self._log_prefix}EllarInjector.get({interface}, scope={scope}) using {binding.provider}"
        )

        result = scope_instance.get(interface, binding.provider).get(
            self.container.injector
        )
        log.debug(f"{self._log_prefix} -> {result}")
        return t.cast(T, result)
