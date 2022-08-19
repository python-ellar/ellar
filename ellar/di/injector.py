import typing as t
from collections import OrderedDict, defaultdict
from inspect import isabstract

from injector import (
    Binder as InjectorBinder,
    Binding,
    Injector,
    Module as InjectorModule,
)

from ellar.compatible import asynccontextmanager
from ellar.constants import MODULE_REF_TYPES
from ellar.helper import get_name
from ellar.logger import logger as log
from ellar.types import T

from .providers import InstanceProvider, Provider
from .scopes import (
    DIScope,
    RequestScope,
    ScopeDecorator,
    SingletonScope,
    TransientScope,
)
from .service_config import get_scope

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.modules import ModuleBase, ModuleRefBase, ModuleTemplateRef


class RequestServiceProvider(InjectorBinder):
    __slots__ = ("_bindings", "_log_prefix", "_context")

    def __init__(self, container: "Container", auto_bind: bool = False) -> None:
        super(RequestServiceProvider, self).__init__(
            injector=container.injector, parent=container, auto_bind=auto_bind
        )
        self._context: t.Dict = {}
        self._log_prefix = container.injector._log_prefix

    def get(self, interface: t.Type[T]) -> T:
        binding, binder = self.get_binding(interface)
        scope = binding.scope
        if isinstance(scope, ScopeDecorator):
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
        result = scope_instance.get(
            interface, binding.provider, context=self._context
        ).get(self.injector)
        log.debug("%s -> %r", self._log_prefix, result)
        return t.cast(T, result)

    def update_context(self, interface: t.Type[T], value: T) -> None:
        assert not isinstance(value, type), f"value must be an object of {interface}"
        _context = {
            interface: Binding(interface, InstanceProvider(value), RequestScope)
        }
        if isinstance(value, Provider):
            _context = {interface: Binding(interface, value, RequestScope)}
        self._bindings.update(_context)

    def dispose(self) -> None:
        del self._context
        del self.parent
        del self.injector


class Container(InjectorBinder):
    __slots__ = ("injector", "_auto_bind", "_bindings", "parent")

    injector: "EllarInjector"

    @t.no_type_check
    def create_binding(
        self,
        interface: t.Type,
        to: t.Any = None,
        scope: t.Union[ScopeDecorator, t.Type[DIScope]] = None,
    ) -> Binding:
        provider = self.provider_for(interface, to)
        scope = scope or getattr(to or interface, "__scope__", TransientScope)
        if isinstance(scope, ScopeDecorator):
            scope = scope.scope
        return Binding(interface, provider, scope)

    def register_binding(self, interface: t.Type, binding: Binding) -> None:
        self._bindings[interface] = binding

    @t.no_type_check
    def register(
        self,
        base_type: t.Type,
        concrete_type: t.Union[t.Type[T], t.Type, T] = None,
        scope: t.Union[t.Type[DIScope], ScopeDecorator] = None,
    ) -> None:
        try:
            if concrete_type and isinstance(concrete_type, type):
                assert issubclass(concrete_type, base_type), (
                    f"Cannot register {get_name(base_type)} for abstract class "
                    f"{get_name(concrete_type)}"
                )
        except TypeError:
            # ignore generic types issues
            pass

        provider = self.provider_for(base_type, concrete_type)
        _scope: t.Any = scope or get_scope(base_type) or TransientScope
        if isinstance(scope, ScopeDecorator):
            _scope = scope.scope
        self.register_binding(base_type, Binding(base_type, provider, _scope))

    def register_instance(
        self, instance: T, concrete_type: t.Union[t.Type[T], Provider] = None
    ) -> None:
        assert not isinstance(instance, type)
        _concrete_type = instance.__class__ if not concrete_type else concrete_type
        self.register(_concrete_type, instance, scope=SingletonScope)

    def register_singleton(
        self,
        base_type: t.Type[T],
        concrete_type: t.Union[t.Type[T], T, Provider] = None,
    ) -> None:
        if not concrete_type:
            self.register_exact_singleton(base_type)
        self.register(base_type, concrete_type, scope=SingletonScope)

    def register_transient(
        self,
        base_type: t.Type,
        concrete_type: t.Union[t.Type, Provider] = None,
    ) -> None:
        if not concrete_type:
            self.register_exact_transient(base_type)
        self.register(base_type, concrete_type, scope=TransientScope)

    def register_scoped(
        self,
        base_type: t.Type,
        concrete_type: t.Union[t.Type, Provider] = None,
    ) -> None:
        if not concrete_type:
            self.register_exact_scoped(base_type)
        self.register(base_type, concrete_type, scope=RequestScope)

    def register_exact_singleton(self, concrete_type: t.Type) -> None:
        assert not isabstract(concrete_type)
        self.register(base_type=concrete_type, scope=SingletonScope)

    def register_exact_transient(self, concrete_type: t.Type) -> None:
        assert not isabstract(concrete_type)
        self.register(base_type=concrete_type, scope=TransientScope)

    def register_exact_scoped(self, concrete_type: t.Type) -> None:
        assert not isabstract(concrete_type)
        self.register(base_type=concrete_type, scope=RequestScope)

    @t.no_type_check
    def install(
        self,
        module: t.Union[t.Type["ModuleBase"], "ModuleBase"],
        **init_kwargs: t.Any,
    ) -> t.Union[InjectorModule, "ModuleBase"]:
        # TODO: move install core to application module
        #   create a ModuleWrapper with init_kwargs

        """Install a module into this container[binder].

        In this context the module is one of the following:

        * function taking the :class:`Container` as it's only parameter

          ::

            def configure(container):
                bind(str, to='s')

            container.install(configure)

        * instance of :class:`Module` (instance of it's subclass counts)

          ::

            class MyModule(StarletteAPIModuleBase):
                def register_services(self, container):
                    container.bind(str, to='s')

            container.install(MyModule())

        * subclass of :class:`Module` - the subclass needs to be instantiable so if it
          expects any parameters they need to be injected

          ::

            container.install(MyModule)
        """

        instance = t.cast(t.Union[t.Type["ModuleBase"], "ModuleBase"], module)

        if isinstance(instance, type) and issubclass(
            t.cast(type, instance), InjectorModule
        ):
            instance = t.cast(type, instance)(**init_kwargs)

        instance(self)
        return instance


class EllarInjector(Injector):
    __slots__ = ("_stack", "parent", "app", "container", "_modules")

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

    @property  # type: ignore
    def binder(self) -> Container:  # type: ignore
        return self.container

    @binder.setter
    def binder(self, value: t.Any) -> None:
        """Nothing happens"""

    @asynccontextmanager
    async def create_request_service_provider(
        self,
    ) -> t.AsyncGenerator[RequestServiceProvider, None]:
        request_provider = RequestServiceProvider(self.container)
        try:
            yield request_provider
        finally:
            request_provider.dispose()
