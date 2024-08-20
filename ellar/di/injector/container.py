import logging
import typing as t

from injector import (
    Binder as InjectorBinder,
)
from injector import (
    Binding,
    UnsatisfiedRequirement,
)
from injector import (
    Module as InjectorModule,
)
from injector import NoScope as TransientScope
from injector import Scope as InjectorScope

from ..scopes import (
    ScopeDecorator,
)
from ..service_config import get_scope

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.modules import ModuleBase

    from .ellar_injector import EllarInjector

NOT_SET = object()
logger = logging.getLogger("ellar.di")


class Container(InjectorBinder):
    __slots__ = (
        "injector",
        "_auto_bind",
        "_bindings",
        "_bindings_by_tag",
        "parent",
        "_aliases",
        "_exact_aliases",
    )

    injector: "EllarInjector"

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super().__init__(*args, **kwargs)
        self._bindings_by_tag: t.Dict[str, t.Type[t.Any]] = {}

    @t.no_type_check
    def create_binding(
        self,
        interface: t.Type,
        to: t.Any = None,
        scope: t.Union[ScopeDecorator, t.Type[InjectorScope]] = None,
    ) -> Binding:
        provider = self.provider_for(interface, to)
        scope = scope or get_scope(to or interface) or TransientScope
        if isinstance(scope, ScopeDecorator):
            scope = scope.scope
        return Binding(interface, provider, scope)

    def get_interface_by_tag(self, tag: str) -> t.Type[t.Any]:
        interface = self._bindings_by_tag.get(tag)
        if interface:
            return interface
        if isinstance(self.parent, Container):
            return self.parent.get_interface_by_tag(tag)

        raise UnsatisfiedRequirement(None, t.cast(t.Any, tag))

    def register_binding(
        self, interface: t.Type, binding: Binding, tag: t.Optional[str] = None
    ) -> None:
        self._bindings[interface] = binding

        if tag:
            self._bindings_by_tag[tag] = interface

    @t.no_type_check
    def register(
        self,
        base_type: t.Type,
        concrete_type: t.Union[t.Type, t.Any] = None,
        scope: t.Union[t.Type[InjectorScope], ScopeDecorator] = None,
        tag: t.Optional[str] = None,
    ) -> None:
        try:
            if concrete_type and isinstance(concrete_type, type):
                assert issubclass(concrete_type, base_type), (
                    f"Cannot register {base_type.__name__} for abstract class "
                    f"{concrete_type.__name__}"
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

        self.register_binding(base_type, Binding(base_type, provider, _scope), tag=tag)

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
        elif isinstance(instance, type):
            return self.injector.get(instance)
        elif not isinstance(instance, type) and not isinstance(
            instance, InjectorModule
        ):
            return instance

        instance(self)
        return instance

    def get_binding(self, interface: t.Type) -> t.Tuple[Binding, InjectorBinder]:
        try:
            return super().get_binding(interface)
        except (KeyError, UnsatisfiedRequirement) as uex:
            try:
                if self.injector.owner:
                    module_name = (
                        self.injector.owner.name if self.injector.owner else None
                    )

                    module_owner = self.injector.tree_manager.search_module_tree(
                        filter_item=lambda data: data.name == module_name,
                        find_predicate=lambda data: interface in data.exports,
                    )

                    if module_owner and module_owner.is_ready:
                        # TODO: possible circular import
                        return module_owner.value.container._get_binding(interface)

            except (KeyError, UnsatisfiedRequirement, Exception) as ex:
                logger.error(
                    f"Ensure {interface} is exported by a module. eg @Module(exports=[{interface}])"
                )
                logger.exception(ex)
            raise UnsatisfiedRequirement(None, interface) from uex
