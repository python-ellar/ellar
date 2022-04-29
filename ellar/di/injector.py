import typing as t
from inspect import isabstract

from injector import (
    Binder as InjectorBinder,
    Binding,
    Injector,
    Module as InjectorModule,
)

from ellar.compatible import asynccontextmanager
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

if t.TYPE_CHECKING:
    from ellar.core.modules import BaseModuleDecorator, ModuleBase


class RequestServiceProvider(InjectorBinder):
    __slots__ = ("_bindings", "_log_prefix", "_context")

    def __init__(self, container: "Container") -> None:
        super(RequestServiceProvider, self).__init__(
            injector=container.injector, parent=container, auto_bind=False
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
            "%StarletteInjector.get(%r, scope=%r) using %r",
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

    injector: "StarletteInjector"

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

    def add_binding(self, interface: t.Type, binding: Binding) -> None:
        self._bindings[interface] = binding

    @t.no_type_check
    def register(
        self,
        base_type: t.Type,
        concrete_type: t.Optional[t.Union[t.Type[T], T]] = None,
        scope: t.Union[t.Type[DIScope], ScopeDecorator] = TransientScope,
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
        _scope: t.Any = scope
        if isinstance(scope, ScopeDecorator):
            _scope = scope.scope
        self.add_binding(base_type, Binding(base_type, provider, _scope))

    def add_instance(
        self, instance: T, concrete_type: t.Optional[t.Type[T]] = None
    ) -> None:
        assert not isinstance(instance, type)
        _concrete_type = instance.__class__ if not concrete_type else concrete_type
        self.register(_concrete_type, instance, scope=SingletonScope)

    def add_singleton(
        self,
        base_type: t.Type[T],
        concrete_type: t.Optional[t.Union[t.Type[T], T]] = None,
    ) -> None:
        if not concrete_type:
            self.add_exact_singleton(base_type)
        self.register(base_type, concrete_type, scope=SingletonScope)

    def add_transient(
        self, base_type: t.Type, concrete_type: t.Optional[t.Type] = None
    ) -> None:
        if not concrete_type:
            self.add_exact_transient(base_type)
        self.register(base_type, concrete_type, scope=TransientScope)

    def add_scoped(
        self, base_type: t.Type, concrete_type: t.Optional[t.Type] = None
    ) -> None:
        if not concrete_type:
            self.add_exact_scoped(base_type)
        self.register(base_type, concrete_type, scope=RequestScope)

    def add_exact_singleton(self, concrete_type: t.Type) -> None:
        assert not isabstract(concrete_type)
        self.register(base_type=concrete_type, scope=SingletonScope)

    def add_exact_transient(self, concrete_type: t.Type) -> None:
        assert not isabstract(concrete_type)
        self.register(base_type=concrete_type, scope=TransientScope)

    def add_exact_scoped(self, concrete_type: t.Type) -> None:
        assert not isabstract(concrete_type)
        self.register(base_type=concrete_type, scope=RequestScope)

    @t.no_type_check
    def install(
        self,
        module: t.Union[t.Type["ModuleBase"], "ModuleBase", "BaseModuleDecorator"],
        **init_kwargs: t.Any,
    ) -> t.Union[InjectorModule, "ModuleBase", "BaseModuleDecorator"]:
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
        if not isinstance(instance, type) and hasattr(instance, "get_module"):
            instance = t.cast("BaseModuleDecorator", module).get_module()

        if isinstance(instance, type) and issubclass(
            t.cast(type, instance), InjectorModule
        ):
            instance = t.cast(type, instance)(**init_kwargs)

        instance(self)
        return instance


class StarletteInjector(Injector):
    __slots__ = (
        "_stack",
        "parent",
        "app",
        "container",
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
        self.container.add_instance(self, StarletteInjector)
        self.container.add_instance(self.binder)

    @property  # type: ignore
    def binder(self) -> Container:  # type: ignore
        return self.container

    @binder.setter
    def binder(self, value: t.Any) -> None:
        ...

    @asynccontextmanager
    async def create_request_service_provider(
        self,
    ) -> t.AsyncGenerator[RequestServiceProvider, None]:
        request_provider = RequestServiceProvider(self.container)
        try:
            yield request_provider
        finally:
            request_provider.dispose()
