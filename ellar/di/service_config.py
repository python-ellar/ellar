import typing as t

from ellar.di.constants import (
    INJECTABLE_ATTRIBUTE,
    INJECTABLE_WATERMARK,
    Tag,
)
from ellar.di.exceptions import DIImproperConfiguration
from ellar.di.types import T
from ellar.reflect import fail_silently, reflect
from injector import (
    CallableT,
    ConstructorOrClassT,
    Scope,
    ScopeDecorator,
    SingletonScope,
    inject,
)
from injector import (
    is_decorated_with_inject as injector_is_decorated_with_inject,
)

if t.TYPE_CHECKING:  # pragma: no cover
    from .injector import Container

__all__ = (
    "ProviderConfig",
    "injectable",
    "is_decorated_with_injectable",
    "get_scope",
    "has_binding",
    "InjectByTag",
)


class ProviderConfig(t.Generic[T]):
    """
    ProviderConfig is a class that configures a provider for a service.

    Example:

    >>> class SomeClass:
    ...     def __init__(self, a: InjectByTag('A'), b: AnotherType):
    ...         self.a = a
    ...         self.b = b

    >>> provider_config = ProviderConfig(SomeClass)
    >>> provider_config.register(container)

    Example with string:

    >>> provider_config = ProviderConfig('path.to:SomeClass')
    >>> provider_config.register(container)

    Example with value:

    >>> provider_config = ProviderConfig(SomeClass, use_value=SomeValue)
    >>> provider_config.register(container)

    Example with class:

    >>> provider_config = ProviderConfig(SomeClass, use_class=AnotherType)
    >>> provider_config.register(container)

    Example with use_class as string:

    >>> provider_config = ProviderConfig(SomeClass, use_class='path.to:AnotherType')
    >>> provider_config.register(container)

    Example with scope:

    >>> provider_config = ProviderConfig(SomeClass, scope=request_scope)
    >>> provider_config.register(container)

    Example with tag:

    >>> provider_config = ProviderConfig(SomeClass, tag='some_tag')
    >>> provider_config.register(container)
    >>> instance = container.get(InjectByTag('some_tag'))
    >>> assert isinstance(instance, SomeClass)


    """

    __slots__ = (
        "base_type",
        "use_value",
        "use_class",
        "scope",
        "tag",
        "export",
        "core",
    )

    def __init__(
        self,
        base_type: t.Union[t.Type[T], t.Type, str],
        *,
        use_value: t.Optional[T] = None,
        use_class: t.Union[t.Type[T], t.Any] = None,
        scope: t.Optional[t.Union[t.Type[Scope], t.Any]] = None,
        tag: t.Optional[str] = None,
        export: bool = False,
        core: bool = False,
    ):
        self.scope = scope or SingletonScope
        if use_value and use_class:
            raise DIImproperConfiguration(
                "`use_class` and `use_value` can not be used at the same time."
            )

        self.base_type = base_type
        self.use_value = use_value
        self.use_class = use_class
        self.tag = tag
        self.export = export
        self.core = core

    def get_type(self) -> t.Type:
        return self._resolve_type(self.base_type)

    def get_use_class(self) -> t.Type:
        return self._resolve_type(self.use_class)

    def _resolve_type(self, type_or_str: t.Union[t.Type, str]) -> t.Type:
        from ellar.utils.importer import import_from_string

        if isinstance(type_or_str, str):
            return t.cast(t.Type, import_from_string(type_or_str))
        return type_or_str

    def register(self, container: "Container") -> None:
        base_type = self.get_type()
        scope = get_scope(base_type) or self.scope
        use_class = self.get_use_class()

        if use_class:
            scope = get_scope(use_class) or scope
            container.register(
                base_type=base_type,
                concrete_type=use_class,
                scope=scope,
                tag=self.tag,
            )
        elif self.use_value:
            container.register(
                base_type=base_type,
                concrete_type=self.use_value,
                scope=scope,
                tag=self.tag,
            )
        elif not isinstance(base_type, type):
            raise DIImproperConfiguration(
                f"couldn't determine provider setup for {base_type}. "
                f"Please use `ProviderConfig` or `register_services` function in a "
                f"Module to configure the provider"
            )
        else:
            container.register(base_type=base_type, scope=scope, tag=self.tag)


@t.overload
def injectable(
    scope: t.Union[t.Type[Scope], ScopeDecorator, CallableT] = SingletonScope,
) -> t.Union[CallableT, t.Callable[[t.Any], CallableT]]:  # pragma: no cover
    pass


@t.overload
def injectable(
    scope: t.Union[t.Type[Scope], ScopeDecorator, t.Type[T]] = SingletonScope,
) -> t.Union[t.Type[T], t.Callable[[t.Any], t.Type[T]]]:  # pragma: no cover
    pass


def injectable(
    scope: t.Union[t.Type[Scope], ScopeDecorator, ConstructorOrClassT] = SingletonScope,
) -> t.Union[ConstructorOrClassT, t.Callable[[t.Any], ConstructorOrClassT]]:
    """Decorates a callable or Type with inject and Defines Type or callable scope injection scope

    Example use:

    >>> @injectable # default is 'singleton_scope'
    ... class InjectableType2:
    ...     def __init__(self):
    ...         pass
    >>>
    >>> @injectable(scope=request_scope)
    ... class InjectableType3:
    ...     def __init__(self):
    ...         pass
    """

    def _decorator(func_or_class: ConstructorOrClassT) -> ConstructorOrClassT:
        fail_silently(inject, constructor_or_class=func_or_class)
        setattr(func_or_class, INJECTABLE_ATTRIBUTE, scope)

        reflect.define_metadata(INJECTABLE_WATERMARK, True, func_or_class)

        return func_or_class

    if not (
        isinstance(scope, ScopeDecorator)
        or isinstance(scope, type)
        and issubclass(scope, Scope)
    ):
        func_ = scope
        scope = SingletonScope
        return _decorator(func_)  # type: ignore[arg-type]

    return _decorator


def is_decorated_with_injectable(func_or_class: ConstructorOrClassT) -> bool:
    """See if given Type or Call is declared with a scope.

    Example use:
    >>> class NonInjectableType:
    ...     def __init__(self):
    ...         pass

    >>> @injectable
    ... class InjectableType2:
    ...     def __init__(self):
    ...         pass

    >>> is_decorated_with_injectable(NonInjectableType)
    True
    >>>
    >>> is_decorated_with_injectable(InjectableType2)
    True
    """

    return hasattr(func_or_class, INJECTABLE_ATTRIBUTE)


def has_binding(func_or_class: ConstructorOrClassT) -> bool:
    """See if given a Type __init__ or callable has __binding__."""
    if isinstance(func_or_class, type) and hasattr(func_or_class, "__init__"):
        return injector_is_decorated_with_inject(func_or_class.__init__)  # type: ignore[misc]
    return injector_is_decorated_with_inject(func_or_class)


def get_scope(
    func_or_class: ConstructorOrClassT,
) -> t.Optional[t.Union[t.Type[Scope], ScopeDecorator]]:
    """Get scope declared scope if available in a type or callable"""
    return t.cast(
        t.Optional[t.Union[t.Type[Scope], ScopeDecorator]],
        getattr(
            func_or_class,
            INJECTABLE_ATTRIBUTE,
            getattr(func_or_class, "__scope__", None),
        ),
    )


def InjectByTag(tag: str) -> t.Any:
    """
    Inject a provider/service by tag.

    For example:

    class A:
        name = 'A'

    class AnotherType:
        name = 'AnotherType'

    class SomeClass:
        def __init__(self, a: InjectByTag('A'), b: AnotherType):
            self.a = a
            self.b = b

    injector = EllarInjector()
    injector.container.register_exact_scoped(A, tag='A')
    injector.container.register_exact_scoped(AnotherType)
    injector.container.register_exact_scoped(SomeClass)

    instance = injector.get(SomeClass)
    assert instance.a.name == 'A'
    assert instance.b.name == 'AnotherType'

    :param tag: Registered Provider/Service tag name
    :return: typing.Any
    """
    return t.NewType(Tag(tag), Tag)
