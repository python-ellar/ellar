import pytest
from injector import CircularDependency, is_decorated_with_inject

from ellar.di import (
    EllarInjector,
    ProviderConfig,
    get_scope,
    injectable,
    is_decorated_with_injectable,
)
from ellar.di.providers import ClassProvider, ModuleProvider
from ellar.di.scopes import SingletonScope, TransientScope

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
    injector = EllarInjector()
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
    injector = EllarInjector(auto_bind=False)
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
    injector = EllarInjector(auto_bind=False)

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

    assert isinstance(
        injector.get(FooDBCatsRepository), FooDBCatsRepository
    )  # only possible because they are decorated with injectable
    assert isinstance(
        injector.get(AnyDBContext), AnyDBContext
    )  # only possible because they are decorated with injectable


def test_module_provider_works():
    injector = EllarInjector(auto_bind=False)
    ProviderConfig(Foo1, use_value=Foo1()).register(injector.container)

    @injectable
    class ModuleMockSingleton:
        def __init__(self, foo1: Foo1, a: str, b: str) -> None:
            self.foo = foo1
            self.a = a
            self.b = b

    injector.container.register(
        ModuleMockSingleton, ModuleProvider(ModuleMockSingleton, a="A", b="B")
    )
    module_mock_instance = injector.get(ModuleMockSingleton)
    assert module_mock_instance.foo
    assert module_mock_instance.a == "A"
    assert module_mock_instance.b == "B"
    assert module_mock_instance is injector.get(ModuleMockSingleton)
