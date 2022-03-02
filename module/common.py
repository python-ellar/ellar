import typing as t
from injector import inject, ConstructorOrClassT
from starletteapi.di.scopes import ScopeDecorator, DIScope, SingletonScope
from starletteapi.shortcuts import fail_silently


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
