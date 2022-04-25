import pytest
from injector import (
    CircularDependency,
    UnsatisfiedRequirement,
    is_decorated_with_inject,
)

from architek.di import (
    ProviderConfig,
    StarletteInjector,
    get_scope,
    is_decorated_with_injectable,
)
from architek.di.providers import ClassProvider
from architek.di.scopes import SingletonScope, TransientScope

from .examples import (
    AnyDBContext,
    CircularDependencyType,
    Foo1,
    Foo2,
    FooDBCatsRepository,
    IDBContext,
    InjectType,
    InjectType2,
    IRepository,
)


def test_circle_dependency():
    injector = StarletteInjector()
    ProviderConfig(CircularDependencyType).register(injector.container)

    with pytest.raises(CircularDependency):
        injector.get(CircularDependencyType)


def test_injectable_and_scopes():
    class NoneInjectType:
        pass

    assert is_decorated_with_injectable(NoneInjectType) is False
    assert is_decorated_with_injectable(InjectType)
    assert (
        is_decorated_with_inject(InjectType.__init__) is False
    )  # InjectType.__init__ was not implemented

    assert is_decorated_with_injectable(InjectType2)
    assert is_decorated_with_inject(InjectType2.__init__)

    assert get_scope(NoneInjectType) is None
    assert get_scope(InjectType) is SingletonScope
    assert get_scope(InjectType2) is TransientScope


def test_provider_config_registers_correctly():
    injector = StarletteInjector(auto_bind=False)
    providers = [
        ProviderConfig(Foo2),
        ProviderConfig(InjectType2),
        ProviderConfig(Foo1),
    ]  # base_type configuration

    for provider in providers:
        provider.register(injector.container)

    assert injector.container.get_binding(Foo2)[0].scope is SingletonScope
    assert isinstance(injector.container.get_binding(Foo2)[0].provider, ClassProvider)

    assert injector.container.get_binding(InjectType2)[0].scope is TransientScope
    assert isinstance(
        injector.container.get_binding(InjectType2)[0].provider, ClassProvider
    )

    assert injector.get(Foo2) == injector.get(Foo2)  # singleton instances are the same
    assert injector.get(InjectType2) != injector.get(InjectType2)  # transient instance


def test_provider_advance_use_case():
    injector = StarletteInjector(auto_bind=False)

    providers_advance = [
        ProviderConfig(
            IRepository, use_class=FooDBCatsRepository
        ),  # register base type against a concrete_type
        ProviderConfig(
            IDBContext, use_class=AnyDBContext
        ),  # register base type against a concrete_type
        ProviderConfig(Foo1, use_value=Foo1()),  # register concrete_type as singleton
    ]

    for provider in providers_advance:
        provider.register(injector.container)

    repository = injector.get(IRepository)
    db_context = injector.get(IDBContext)
    assert isinstance(repository, FooDBCatsRepository)
    assert isinstance(db_context, AnyDBContext)
    assert repository.context == db_context  # service registered as singleton

    with pytest.raises(UnsatisfiedRequirement):
        injector.get(AnyDBContext)

    with pytest.raises(UnsatisfiedRequirement):
        injector.get(FooDBCatsRepository)

    providers_advance.append(ProviderConfig(AnyDBContext))
    providers_advance.append(ProviderConfig(FooDBCatsRepository))

    injector = StarletteInjector(auto_bind=False)

    for provider in providers_advance:
        provider.register(injector.container)

    assert injector.get(AnyDBContext)
    assert injector.get(FooDBCatsRepository)

    assert isinstance(injector.get(IRepository), FooDBCatsRepository)
    assert isinstance(injector.get(IDBContext), AnyDBContext)
