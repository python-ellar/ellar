import pytest
from ellar.di import EllarInjector, ProviderConfig
from ellar.di.constants import Tag
from injector import UnsatisfiedRequirement

from .examples import (
    AnyDBContext,
    FooDBCatsRepository,
    IDBContext,
    InjectByTagTest,
    TransientRequestContext,
)


def test_registering_provider_by_tags_works():
    injector = EllarInjector(auto_bind=False)
    ProviderConfig(TransientRequestContext, tag="request_context").register(
        injector.container
    )

    instance1 = injector.get("request_context")
    instance2 = injector.get(TransientRequestContext)

    assert isinstance(instance1, TransientRequestContext)
    assert isinstance(instance2, TransientRequestContext)
    assert instance1 != instance2


def test_resolving_invalid_fails():
    injector = EllarInjector(auto_bind=False)
    ProviderConfig(TransientRequestContext, tag="request_context").register(
        injector.container
    )

    assert injector.get("request_context")

    with pytest.raises(UnsatisfiedRequirement):
        injector.get("request_context_2")


def test_resolving_deeply_nested_object_works():
    injector = EllarInjector(auto_bind=False)
    ProviderConfig(TransientRequestContext, tag="request_context").register(
        injector.container
    )

    injector2 = EllarInjector(auto_bind=False, parent=injector)

    instance1 = injector2.get("request_context")
    assert isinstance(instance1, TransientRequestContext)


def test_tag_override():
    injector = EllarInjector()

    injector.container.register(IDBContext, AnyDBContext, tag="connection")
    injector.container.register(FooDBCatsRepository, tag="connection")

    instance = injector.get(Tag("connection"))
    assert not isinstance(instance, AnyDBContext)
    assert isinstance(instance, FooDBCatsRepository)


def test_inject_by_tag():
    injector = EllarInjector()
    injector.container.register(InjectByTagTest)
    injector.container.register(TransientRequestContext)

    injector.container.register(IDBContext, AnyDBContext)
    injector.container.register(FooDBCatsRepository, tag="connection")

    instance1 = injector.get(InjectByTagTest)
    assert isinstance(instance1.context, FooDBCatsRepository)
