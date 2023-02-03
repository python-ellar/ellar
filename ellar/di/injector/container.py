import typing as t
from inspect import isabstract

from injector import (
    AssistedBuilder,
    Binder as InjectorBinder,
    Binding,
    Module as InjectorModule,
    Scope as InjectorScope,
    UnsatisfiedRequirement,
    _is_specialization,
)

from ellar.constants import NOT_SET
from ellar.helper import get_name
from ellar.types import T

from ..providers import Provider
from ..scopes import (
    DIScope,
    RequestScope,
    ScopeDecorator,
    SingletonScope,
    TransientScope,
)
from ..service_config import get_scope, is_decorated_with_injectable

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.modules import ModuleBase

    from .ellar_injector import EllarInjector


class Container(InjectorBinder):
    __slots__ = (
        "injector",
        "_auto_bind",
        "_bindings",
        "parent",
        "_aliases",
        "_exact_aliases",
    )

    injector: "EllarInjector"

    @t.no_type_check
    def create_binding(
        self,
        interface: t.Type,
        to: t.Any = None,
        scope: t.Union[ScopeDecorator, t.Type[DIScope]] = None,
    ) -> Binding:
        provider = self.provider_for(interface, to)
        scope = scope or get_scope(to or interface) or TransientScope
        if isinstance(scope, ScopeDecorator):
            scope = scope.scope
        return Binding(interface, provider, scope)

    def get_binding(self, interface: type) -> t.Tuple[Binding, InjectorBinder]:
        is_scope = isinstance(interface, type) and issubclass(interface, InjectorScope)
        is_assisted_builder = _is_specialization(interface, AssistedBuilder)
        try:
            return self._get_binding(
                interface, only_this_binder=is_scope or is_assisted_builder
            )
        except (KeyError, UnsatisfiedRequirement):
            if is_scope:
                scope = interface
                self.bind(scope, to=scope(self.injector))
                return self._get_binding(interface)
            # The special interface is added here so that requesting a special
            # interface with auto_bind disabled works
            if (
                self._auto_bind
                or self._is_special_interface(interface)
                or is_decorated_with_injectable(interface)
            ):
                binding = self.create_binding(interface)
                self._bindings[interface] = binding
                return binding, self

        raise UnsatisfiedRequirement(None, interface)

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
        except TypeError:  # pragma: no cover
            # ignore generic types issues
            pass

        provider = self.provider_for(base_type, concrete_type)

        _scope: t.Any = scope or NOT_SET

        if _scope is NOT_SET and isinstance(concrete_type, type):
            _scope = get_scope(concrete_type) or TransientScope
        elif _scope is NOT_SET:
            _scope = get_scope(base_type) or TransientScope

        if isinstance(_scope, ScopeDecorator):
            _scope = _scope.scope

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
        """

        :param base_type:
        :param concrete_type:
        :return:
        """
        if not concrete_type:
            self.register_exact_singleton(base_type)
        self.register(base_type, concrete_type, scope=SingletonScope)

    def register_transient(
        self,
        base_type: t.Type,
        concrete_type: t.Union[t.Type, Provider] = None,
    ) -> None:
        """

        :param base_type:
        :param concrete_type:
        :return:
        """
        if not concrete_type:
            self.register_exact_transient(base_type)
        self.register(base_type, concrete_type, scope=TransientScope)

    def register_scoped(
        self,
        base_type: t.Type,
        concrete_type: t.Union[t.Type, Provider] = None,
    ) -> None:
        """

        :param base_type:
        :param concrete_type:
        :return:
        """
        if not concrete_type:
            self.register_exact_scoped(base_type)
        self.register(base_type, concrete_type, scope=RequestScope)

    def register_exact_singleton(self, concrete_type: t.Type) -> None:
        """

        :param concrete_type:
        :return:
        """
        assert not isabstract(concrete_type)
        self.register(base_type=concrete_type, scope=SingletonScope)

    def register_exact_transient(self, concrete_type: t.Type) -> None:
        """

        :param concrete_type:
        :return:
        """
        assert not isabstract(concrete_type)
        self.register(base_type=concrete_type, scope=TransientScope)

    def register_exact_scoped(self, concrete_type: t.Type) -> None:
        """

        :param concrete_type:
        :return:
        """
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
