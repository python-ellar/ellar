import pytest
from injector import Binder, Injector, UnsatisfiedRequirement

from ellar.common import Module
from ellar.core import ModuleBase
from ellar.di import Container, StarletteInjector
from ellar.di.providers import ClassProvider, InstanceProvider

from .examples import Foo, Foo1, Foo2


def test_container_install_module():
    called = False
    app_container = StarletteInjector().container

    class FakeModule(ModuleBase):
        def register_services(self, container: Container) -> None:
            nonlocal called
            called = True

    @Module()
    class DecoratedModule:
        def register_services(self, container: Container) -> None:
            nonlocal called
            called = True

    fake_module = app_container.install(FakeModule)
    assert called
    assert isinstance(fake_module, FakeModule)

    called = False

    decorated_module = app_container.install(DecoratedModule)
    assert called
    assert isinstance(decorated_module, DecoratedModule)


def test_default_container_registration():
    injector = StarletteInjector(auto_bind=False)
    assert isinstance(injector.get(Container), Container)
    assert isinstance(injector.get(StarletteInjector), StarletteInjector)
    assert isinstance(injector.get(StarletteInjector), StarletteInjector)

    with pytest.raises(UnsatisfiedRequirement):
        injector.get(Injector)

    with pytest.raises(UnsatisfiedRequirement):
        injector.get(Binder)


@pytest.mark.asyncio
async def test_request_service_provider():
    injector = StarletteInjector(auto_bind=False)
    injector.container.register_scoped(Foo1)
    injector.container.register_exact_transient(Foo2)

    def assert_attributes(provider, expected):
        assert hasattr(provider, "parent") is expected
        assert hasattr(provider, "injector") is expected
        assert hasattr(provider, "_context") is expected

    async with injector.create_request_service_provider() as request_provider:
        assert_attributes(request_provider, True)
        foo_instance = Foo()
        request_provider.update_context(Foo, foo_instance)
        request_provider.update_context(
            Foo1, Foo1()
        )  # overrides parent provider config for Foo1

        assert isinstance(
            injector.container.get_binding(Foo1)[0].provider, ClassProvider
        )
        assert isinstance(
            request_provider.get_binding(Foo1)[0].provider, InstanceProvider
        )

        assert request_provider.get(Foo) is foo_instance
        # request_provider defaults to parent when binding is not in its context
        assert isinstance(request_provider.get(Foo2), Foo2)

        with pytest.raises(UnsatisfiedRequirement):
            # parent can not resolve bindings added to request service provider
            injector.get(Foo)

    assert_attributes(request_provider, False)
