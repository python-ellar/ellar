import typing as t
from collections import OrderedDict, defaultdict

from ellar.di.logger import log
from ellar.reflect import asynccontextmanager
from injector import Injector, Scope, ScopeDecorator

from ..asgi_args import RequestScopeContext
from ..constants import MODULE_REF_TYPES, SCOPED_CONTEXT_VAR
from ..providers import InstanceProvider, Provider
from ..types import T
from .container import Container

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.modules import (
        ModuleBase,
        ModuleRefBase,
        ModuleSetup,
        ModuleTemplateRef,
    )


class EllarInjector(Injector):
    __slots__ = (
        "_stack",
        "parent",
        "container",
        "_modules",
    )

    def __init__(
        self,
        auto_bind: bool = True,
        parent: t.Optional["Injector"] = None,
    ) -> None:
        self._stack = ()
        self.parent = parent
        # Binder
        self.container = Container(
            self,
            auto_bind=auto_bind,
            parent=parent.binder if parent is not None else None,
        )

        # Bind some useful types
        self.container.register_instance(self, EllarInjector)
        self.container.register_instance(self.binder)
        self._modules: t.DefaultDict = defaultdict(OrderedDict)
        self._modules[MODULE_REF_TYPES.TEMPLATE] = OrderedDict()
        self._modules[MODULE_REF_TYPES.PLAIN] = OrderedDict()
        self._modules[MODULE_REF_TYPES.DYNAMIC] = OrderedDict()
        self._modules[MODULE_REF_TYPES.APP_DEPENDENT] = OrderedDict()

    @property  # type: ignore
    def binder(self) -> Container:
        return self.container

    @binder.setter
    def binder(self, value: t.Any) -> None:
        """Nothing happens"""

    def get_modules(
        self,
    ) -> t.Dict[t.Type["ModuleBase"], "ModuleRefBase"]:
        modules = dict(
            self._modules[MODULE_REF_TYPES.TEMPLATE],
        )
        modules.update(self._modules[MODULE_REF_TYPES.PLAIN])
        return modules

    def get_dynamic_modules(
        self,
    ) -> t.Generator["ModuleSetup", t.Any, None]:
        for _, module_configure in self._modules[MODULE_REF_TYPES.DYNAMIC].items():
            yield module_configure

        self._modules[MODULE_REF_TYPES.DYNAMIC].clear()

    def get_app_dependent_modules(
        self,
    ) -> t.Generator["ModuleSetup", t.Any, None]:
        for _, module_configure in self._modules[
            MODULE_REF_TYPES.APP_DEPENDENT
        ].items():
            yield module_configure

        self._modules[MODULE_REF_TYPES.APP_DEPENDENT].clear()

    def get_module(self, module: t.Type) -> t.Optional["ModuleRefBase"]:
        result: t.Optional["ModuleRefBase"] = None
        if module in self._modules[MODULE_REF_TYPES.TEMPLATE]:
            result = self._modules[MODULE_REF_TYPES.TEMPLATE][module]
            return result

        if module in self._modules[MODULE_REF_TYPES.PLAIN]:
            result = self._modules[MODULE_REF_TYPES.PLAIN][module]
            return result
        return result

    def get_templating_modules(
        self,
    ) -> t.Dict[t.Type["ModuleBase"], "ModuleTemplateRef"]:
        return self._modules.get(  # type:ignore[no-any-return]
            MODULE_REF_TYPES.TEMPLATE, {}
        )

    def add_module(self, module_ref: t.Union["ModuleRefBase", "ModuleSetup"]) -> None:
        self._modules[module_ref.ref_type].update({module_ref.module: module_ref})

    @t.no_type_check
    def get(
        self,
        interface: t.Type[T],
        scope: t.Union[ScopeDecorator, t.Type[Scope]] = None,
    ) -> T:
        binding, binder = self.container.get_binding(interface)
        scope = binding.scope

        if isinstance(scope, ScopeDecorator):  # pragma: no cover
            scope = scope.scope
        # Fetch the corresponding Scope instance from the Binder.
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

    def update_scoped_context(self, interface: t.Type[T], value: T) -> None:
        # Sets RequestScope contexts so that they can be available when needed
        #
        scoped_context = SCOPED_CONTEXT_VAR.get()
        if scoped_context is None:
            return

        if isinstance(value, Provider):
            scoped_context.context.update({interface: value})
        else:
            scoped_context.context.update({interface: InstanceProvider(value)})

    @asynccontextmanager
    async def create_asgi_args(self) -> t.AsyncGenerator["EllarInjector", None]:
        try:
            SCOPED_CONTEXT_VAR.set(RequestScopeContext())
            yield self
        finally:
            SCOPED_CONTEXT_VAR.set(None)
