import typing as t
from injector import inject, ConstructorOrClassT
from starletteapi.di.scopes import ScopeDecorator, DIScope, SingletonScope


class _Injectable:
    def __init__(self, scope: t.Optional[t.Union[t.Type[DIScope], ScopeDecorator]] = None):
        self.scope = scope or SingletonScope

    def __call__(self, func_or_class: ConstructorOrClassT) -> ConstructorOrClassT:
        inject(func_or_class)
        setattr(func_or_class, '__di_scope__', self.scope)
        return func_or_class


def injectable(
        scope: t.Optional[t.Union[t.Type[DIScope], ScopeDecorator]] = None
) -> t.Union[ConstructorOrClassT, t.Callable]:
    if callable(scope):
        _injectable = _Injectable(SingletonScope)
        return _injectable(scope)
    elif not isinstance(scope, ScopeDecorator) or isinstance(scope, type) and not issubclass(scope, DIScope):
        _injectable = _Injectable(SingletonScope)
        return _injectable(scope)
    return _Injectable(scope)
