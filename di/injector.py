import sys
from inspect import isabstract
from typing import Type, Union, TYPE_CHECKING, TypeVar, Optional, Dict, cast, Any, Callable
from injector import Injector, Binder as InjectorBinder, Binding
from starletteapi.context import ExecutionContext
from .scopes import DIScope, ScopeDecorator, TransientScope, SingletonScope, RequestScope
from .providers import InstanceProvider
from starletteapi.logger import logger as log

from starletteapi.helper import get_name

if TYPE_CHECKING:
    from starletteapi.main import StarletteApp
    from starletteapi.module import ApplicationModuleBase

T = TypeVar("T")


class DIRequestServiceProvider:
    def __init__(self, container: 'Container', context: Optional[Dict]) -> None:
        self.injector = container.injector
        self.container = container
        self.context = context

    def get(self, interface: Type[T]) -> T:
        binding, binder = self.container.get_binding(interface)
        scope = binding.scope
        if isinstance(scope, ScopeDecorator):
            scope = scope.scope
        # Fetch the corresponding Scope instance from the Binder.
        scope_binding, _ = binder.get_binding(scope)
        scope_instance = cast(DIScope, scope_binding.provider.get(self))

        log.debug(
            '%StarletteInjector.get(%r, scope=%r) using %r', self.injector._log_prefix, interface, scope,
            binding.provider
        )
        result = scope_instance.get(interface, binding.provider, context=self.context).get(self.injector)
        log.debug('%s -> %r', self.injector._log_prefix, result)
        return result

    def update_context(self, interface: Type[T], value: T) -> None:
        self.context.update({interface: InstanceProvider(value)})


class Container(InjectorBinder):
    def create_binding(
            self, interface: type, to: Any = None, scope: Union[ScopeDecorator, Type[DIScope]] = None
    ) -> Binding:
        provider = self.provider_for(interface, to)
        scope = scope or getattr(to or interface, '__scope__', TransientScope)
        if isinstance(scope, ScopeDecorator):
            scope = scope.scope
        return Binding(interface, provider, scope)

    def add_binding(self, interface: Type, binding: Binding) -> None:
        self._bindings[interface] = binding

    def register(
            self,
            base_type: Type,
            concrete_type: Union[Type, None] = None,
            scope: Union[Type[DIScope], ScopeDecorator] = TransientScope
    ):
        try:
            assert issubclass(concrete_type, base_type), (
                f"Cannot register {get_name(base_type)} for abstract class "
                f"{get_name(concrete_type)}"
            )
        except TypeError:
            # ignore, this happens with generic types
            pass

        provider = self.provider_for(base_type, concrete_type)
        if isinstance(scope, ScopeDecorator):
            scope = scope.scope
        self.add_binding(base_type, Binding(base_type, provider, scope))

    def add_instance(
            self, instance: T,
            concrete_type: Optional[Type[T]] = None
    ) -> None:
        assert not isinstance(instance, type)
        concrete_type = instance.__class__ if not concrete_type else concrete_type
        self.register(concrete_type, instance)

    def add_singleton(self, base_type: Type[T], concrete_type: Optional[Type[T]] = None) -> None:
        if not concrete_type:
            self.add_exact_singleton(concrete_type)
        self.register(base_type, concrete_type, scope=SingletonScope)

    def add_transient(self, base_type: Type, concrete_type: Optional[Type] = None) -> None:
        if not concrete_type:
            self.add_exact_singleton(concrete_type)
        self.register(base_type, concrete_type, scope=TransientScope)

    def add_scoped(self, base_type: Type, concrete_type: Optional[Type] = None) -> None:
        if not concrete_type:
            self.add_exact_singleton(concrete_type)
        self.register(base_type, concrete_type, scope=TransientScope)

    def add_exact_singleton(self, concrete_type: Type[T]) -> None:
        assert not isabstract(concrete_type)
        self.register(base_type=concrete_type, scope=SingletonScope)

    def add_exact_transient(self, concrete_type: Type[T]) -> None:
        assert not isabstract(concrete_type)
        self.register(base_type=concrete_type, scope=TransientScope)

    def add_exact_scoped(self, concrete_type: Type[T], ) -> None:
        assert not isabstract(concrete_type)
        self.register(base_type=concrete_type, scope=RequestScope)


class StarletteInjector(Injector):
    def __init__(
            self,
            app: 'StarletteApp',
            root_module: Type['ApplicationModuleBase'],
            auto_bind: bool = True,
            parent: 'Injector' = None,
    ):
        self._stack = ()

        self.parent = parent
        self.app = app
        # Binder
        self.container = Container(
            self, auto_bind=auto_bind, parent=parent.binder if parent is not None else None
        )
        self.binder = self.container

        self.root_module = root_module
        # Bind some useful types
        self.container.add_instance(self, StarletteInjector)
        self.container.add_instance(self.binder)
        self.container.add_exact_scoped(ExecutionContext)

        # Initialise modules
        self.container.install(root_module)

    def create_di_request_service_provider(self, context: Dict) -> DIRequestServiceProvider:
        return DIRequestServiceProvider(self.container, context)

