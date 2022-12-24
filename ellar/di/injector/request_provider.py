import typing as t

from injector import Binder as InjectorBinder, Binding

from ellar.logger import logger as log
from ellar.types import T

from ..providers import InstanceProvider, Provider
from ..scopes import DIScope, RequestScope, ScopeDecorator

if t.TYPE_CHECKING:  # pragma: no cover
    from .container import Container


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
