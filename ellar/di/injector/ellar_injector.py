import typing as t
from collections import OrderedDict, defaultdict

from injector import Injector

from ellar.asgi_args import RequestScopeContext
from ellar.compatible import asynccontextmanager
from ellar.constants import MODULE_REF_TYPES, SCOPED_CONTEXT_VAR
from ellar.logger import logger as log
from ellar.types import T

from ..providers import InstanceProvider, Provider
from ..scopes import DIScope, ScopeDecorator
from .container import Container

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.modules import ModuleBase, ModuleRefBase, ModuleTemplateRef


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
        parent: "Injector" = None,
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

    @property  # type: ignore
    def binder(self) -> Container:  # type: ignore
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
        return self._modules.get(MODULE_REF_TYPES.TEMPLATE, {})

    def add_module(self, module_ref: "ModuleRefBase") -> None:
        self._modules[module_ref.ref_type].update({module_ref.module: module_ref})

    @t.no_type_check
    def get(
        self,
        interface: t.Type[T],
        scope: t.Union[ScopeDecorator, t.Type[DIScope]] = None,
    ) -> T:
        scoped_context = SCOPED_CONTEXT_VAR.get()
        context = None
        if scoped_context:
            context = scoped_context.context

        binding, binder = self.container.get_binding(interface)
        scope = binding.scope

        if isinstance(scope, ScopeDecorator):  # pragma: no cover
            scope = scope.scope
        # Fetch the corresponding Scope instance from the Binder.
        scope_binding, _ = binder.get_binding(scope)
        scope_instance = t.cast(DIScope, scope_binding.provider.get(self))

        log.debug(
            "%EllarInjector.get(%r, scope=%r) using %r",
            self._log_prefix,
            interface,
            scope,
            binding.provider,
        )

        result = scope_instance.get(interface, binding.provider, context=context).get(
            self.container.injector
        )
        log.debug("%s -> %r", self._log_prefix, result)
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
