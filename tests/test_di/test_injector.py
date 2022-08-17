from collections import OrderedDict

import pytest
from injector import Binder, Injector, UnsatisfiedRequirement

from ellar.common import Module
from ellar.constants import MODULE_REF_TYPES
from ellar.core import Config, ModuleBase
from ellar.core.modules.ref import create_module_ref_factor
from ellar.di import Container, EllarInjector
from ellar.di.providers import ClassProvider, InstanceProvider

from .examples import Foo, Foo1, Foo2


class EllarTestPlainModule(ModuleBase):
    pass


@Module(template_folder="some_template")
class EllarTestTemplateModule(ModuleBase):
    pass


def test_container_install_module():
    called = False
    app_container = EllarInjector().container

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
    injector = EllarInjector(auto_bind=False)
    assert isinstance(injector.get(Container), Container)
    assert isinstance(injector.get(EllarInjector), EllarInjector)
    assert isinstance(injector.get(EllarInjector), EllarInjector)

    with pytest.raises(UnsatisfiedRequirement):
        injector.get(Injector)

    with pytest.raises(UnsatisfiedRequirement):
        injector.get(Binder)


@pytest.mark.asyncio
async def test_request_service_provider():
    injector = EllarInjector(auto_bind=False)
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


class TestInjectorModuleFunctions:
    def setup(self):
        self.injector = EllarInjector()
        config = Config()

        assert isinstance(
            self.injector._modules[MODULE_REF_TYPES.TEMPLATE], OrderedDict
        )
        assert isinstance(self.injector._modules[MODULE_REF_TYPES.PLAIN], OrderedDict)

        self.module_plain_ref = create_module_ref_factor(
            EllarTestPlainModule, config=config, container=self.injector.container
        )
        self.module_template_ref = create_module_ref_factor(
            EllarTestTemplateModule, config=config, container=self.injector.container
        )

    def test_injector_add_module(self):
        self.injector.add_module(self.module_plain_ref)
        self.injector.add_module(self.module_template_ref)

        assert len(self.injector._modules[MODULE_REF_TYPES.TEMPLATE]) == 1
        assert len(self.injector._modules[MODULE_REF_TYPES.PLAIN]) == 1

        assert (
            list(self.injector._modules[MODULE_REF_TYPES.PLAIN].values())[0]
            is self.module_plain_ref
        )
        assert (
            list(self.injector._modules[MODULE_REF_TYPES.TEMPLATE].values())[0]
            is self.module_template_ref
        )

    def test_injector_get_module_works(self):
        self.injector.add_module(self.module_plain_ref)

        module_ref = self.injector.get_module(EllarTestPlainModule)
        assert module_ref is self.module_plain_ref

        module_ref = self.injector.get_module(EllarTestTemplateModule)
        assert module_ref is None

        self.injector.add_module(self.module_template_ref)
        module_ref = self.injector.get_module(EllarTestTemplateModule)
        assert module_ref is self.module_template_ref

    def test_injector_get_templating_modules_works(self):
        modules = self.injector.get_templating_modules()
        assert len(modules) == 0

        self.injector.add_module(self.module_plain_ref)
        modules = self.injector.get_templating_modules()
        assert len(modules) == 0

        self.injector.add_module(self.module_template_ref)
        modules = self.injector.get_templating_modules()
        assert len(modules) == 1

    def test_injector_get_modules_works(self):
        modules = self.injector.get_modules()
        assert len(modules) == 0

        self.injector.add_module(self.module_plain_ref)
        modules = self.injector.get_modules()
        assert len(modules) == 1

        self.injector.add_module(self.module_template_ref)
        modules = self.injector.get_modules()
        assert len(modules) == 2
