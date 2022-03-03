import typing as t
from .injector import Container
from .scopes import DIScope, ScopeDecorator, SingletonScope
from injector import inject, ConstructorOrClassT
from starletteapi.shortcuts import fail_silently

T = t.TypeVar('T')

__all__ = ('ServiceConfig', 'injectable')


class ServiceConfig:
    __slots__ = ('base_type', 'use_value', 'use_class')

    def __init__(
            self,
            base_type: t.Type[T],
            *,
            use_value: t.Optional[T] = None,
            use_class: t.Optional[t.Type[T]] = None
    ):
        self.base_type = base_type
        self.use_value = use_value
        self.use_class = use_class

    def register(self, container: Container):
        scope = t.cast(
            t.Union[t.Type[DIScope], ScopeDecorator],
            getattr(self.base_type, '__di_scope__', SingletonScope)
        )
        if self.use_class:
            scope = t.cast(
                t.Union[t.Type[DIScope], ScopeDecorator],
                getattr(self.use_class, '__di_scope__', SingletonScope)
            )
            container.register(base_type=self.base_type, concrete_type=self.use_class, scope=scope)
        elif self.use_value:
            container.add_singleton(base_type=self.base_type, concrete_type=self.use_value)
        else:
            container.register(base_type=self.base_type, scope=scope)


class _Injectable:
    def __init__(self, scope: t.Optional[t.Union[t.Type[DIScope], ScopeDecorator]] = None):
        self.scope = scope or SingletonScope

    def __call__(self, func_or_class: ConstructorOrClassT) -> ConstructorOrClassT:
        fail_silently(inject, constructor_or_class=func_or_class)
        setattr(func_or_class, '__di_scope__', self.scope)
        return func_or_class


def injectable(
        scope: t.Optional[t.Union[t.Type[DIScope], ScopeDecorator]]
) -> t.Union[ConstructorOrClassT, t.Callable]:
    if isinstance(scope, ScopeDecorator) or isinstance(scope, type) and issubclass(scope, DIScope):
        return _Injectable(scope)
    _injectable = _Injectable(SingletonScope)
    return _injectable(scope)
