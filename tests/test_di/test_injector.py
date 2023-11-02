from collections import OrderedDict

import pytest
from ellar.common import Module
from ellar.core import Config, ModuleBase
from ellar.core.modules.ref import create_module_ref_factor
from ellar.di import MODULE_REF_TYPES, SCOPED_CONTEXT_VAR, Container, EllarInjector
from ellar.di.providers import ClassProvider, InstanceProvider
from injector import Binder, Injector, UnsatisfiedRequirement

from .examples import Foo, Foo1, Foo2


class EllarTestPlainModule(ModuleBase):
    pass


@Module(template_folder="some_template")
class EllarTestTemplateModule(ModuleBase):
    pass


def test_container_install_module_case_1():
    called = False
    app_container = EllarInjector().container

    class PlainModule(ModuleBase):
        def register_services(self, container: Container) -> None:
            nonlocal called
            called = True

    @Module()
    class DecoratedModuleWithBase(ModuleBase):
        def register_services(self, container: Container) -> None:
            nonlocal called
            called = True

    plain_module = app_container.install(PlainModule)
    assert called
    assert isinstance(plain_module, PlainModule)

    called = False

    decorated_module = app_container.install(DecoratedModuleWithBase)
    assert called
    assert isinstance(decorated_module, DecoratedModuleWithBase)

    called = False
    app_container.install(PlainModule())
    assert called

    called = False

    app_container.install(DecoratedModuleWithBase())
    assert called


def test_container_install_module_return_case_2():
    called = False
    app_container = EllarInjector().container

    @Module()
    class DecoratedModule:
        def register_services(self, container: Container) -> None:
            nonlocal called
            called = True

    decorated_module = app_container.install(DecoratedModule)
    assert called is False
    assert isinstance(decorated_module, DecoratedModule)

    decorated_module = app_container.install(DecoratedModule())
    assert called is False
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
async def test_request_service_context():
    injector = EllarInjector(auto_bind=False)
    injector.container.register_scoped(Foo1)
    injector.container.register_exact_transient(Foo2)

    async with injector.create_asgi_args():
        asgi_context = SCOPED_CONTEXT_VAR.get()

        foo1 = injector.get(Foo1)  # result will be tracked by asgi_context
        injector.get(Foo2)  # registered as transient scoped

        assert isinstance(asgi_context.context[Foo1], InstanceProvider)
        assert asgi_context.context.get(Foo2) is None

        # transient scoped
        foo2 = injector.get(Foo2)
        assert isinstance(foo2, Foo2)
        assert injector.get(Foo2) != foo2  # transient scoped

        assert injector.get(Foo1) == foo1  # still within the context....

        with pytest.raises(UnsatisfiedRequirement):
            injector.get(Foo)

    with pytest.raises(UnsatisfiedRequirement):
        injector.get(Foo1)


@pytest.mark.asyncio
async def test_injector_update_scoped_context():
    injector = EllarInjector(auto_bind=False)

    async with injector.create_asgi_args():
        asgi_context = SCOPED_CONTEXT_VAR.get()

        injector.update_scoped_context(Foo1, Foo1())
        injector.update_scoped_context(Foo, ClassProvider(Foo))

        assert isinstance(asgi_context.context[Foo1], InstanceProvider)
        assert isinstance(asgi_context.context[Foo], ClassProvider)

    injector.update_scoped_context(Foo1, Foo1())
    assert SCOPED_CONTEXT_VAR.get() is None


class TestInjectorModuleFunctions:
    def setup_method(self):
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
