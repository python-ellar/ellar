import pytest
from ellar.common import Module
from ellar.core import ForwardRefModule
from ellar.di import ProviderConfig
from ellar.testing import Test
from injector import UnsatisfiedRequirement

from .examples import (
    AnyDBContext,
    Foo1,
    FooDBCatsRepository,
    IDBContext,
    IRepository,
)


def test_module_providers_are_enclosed_to_the_module():
    @Module(
        name="moduleA",
        providers=[
            ProviderConfig(IRepository, use_class=FooDBCatsRepository),
            ProviderConfig(IDBContext, use_class=AnyDBContext),
        ],
    )
    class ModuleA:
        pass

    @Module(name="moduleB", providers=[ProviderConfig(Foo1, use_value=Foo1())])
    class ModuleB:
        pass

    app = Test.create_test_module(modules=[ModuleA, ModuleB]).create_application()

    with pytest.raises(UnsatisfiedRequirement):
        app.injector.get(IRepository)

    with pytest.raises(UnsatisfiedRequirement):
        app.injector.get(IDBContext)

    with pytest.raises(UnsatisfiedRequirement):
        app.injector.get(Foo1)

    moduleB = app.injector.tree_manager.get_module(ModuleB).value
    assert isinstance(moduleB.container.injector.get(Foo1), Foo1)

    with pytest.raises(UnsatisfiedRequirement):
        moduleB.container.injector.get(IRepository)

    with pytest.raises(UnsatisfiedRequirement):
        moduleB.container.injector.get(IDBContext)

    moduleA = app.injector.tree_manager.get_module(ModuleA).value
    assert isinstance(moduleA.container.injector.get(IRepository), IRepository)
    assert isinstance(moduleA.container.injector.get(IDBContext), IDBContext)

    with pytest.raises(UnsatisfiedRequirement):
        moduleA.container.injector.get(Foo1)


def test_module_providers_export_works_for_root_module():
    @Module(
        name="moduleA",
        providers=[
            ProviderConfig(IRepository, use_class=FooDBCatsRepository),
            ProviderConfig(IDBContext, use_class=AnyDBContext),
        ],
        exports=[IRepository, IDBContext],
    )
    class ModuleA:
        pass

    @Module(
        name="moduleB", providers=[ProviderConfig(Foo1, use_value=Foo1(), export=True)]
    )
    class ModuleB:
        pass

    app = Test.create_test_module(modules=[ModuleA, ModuleB]).create_application()
    assert isinstance(app.injector.get(IRepository), IRepository)
    assert isinstance(app.injector.get(IDBContext), IDBContext)

    moduleB = app.injector.tree_manager.get_module(ModuleB).value

    with pytest.raises(UnsatisfiedRequirement):
        moduleB.container.injector.get(IRepository)

    with pytest.raises(UnsatisfiedRequirement):
        moduleB.container.injector.get(IDBContext)

    moduleA = app.injector.tree_manager.get_module(ModuleA).value

    with pytest.raises(UnsatisfiedRequirement):
        moduleA.container.injector.get(Foo1)


def test_module_providers_export_works_for_referenced_module():
    @Module(
        name="moduleA",
        providers=[
            ProviderConfig(IRepository, use_class=FooDBCatsRepository),
            ProviderConfig(IDBContext, use_class=AnyDBContext),
        ],
        exports=[IRepository, IDBContext],
    )
    class ModuleA:
        pass

    @Module(
        name="moduleB",
        modules=[ForwardRefModule(module_name="moduleA")],
        providers=[ProviderConfig(Foo1, use_value=Foo1(), export=True)],
    )
    class ModuleB:
        pass

    app = Test.create_test_module(modules=[ModuleA, ModuleB]).create_application()
    assert isinstance(app.injector.get(IRepository), IRepository)
    assert isinstance(app.injector.get(IDBContext), IDBContext)

    moduleB = app.injector.tree_manager.get_module(ModuleB).value

    assert isinstance(moduleB.container.injector.get(IRepository), IRepository)
    assert isinstance(moduleB.container.injector.get(IDBContext), IDBContext)

    moduleA = app.injector.tree_manager.get_module(ModuleA).value

    with pytest.raises(UnsatisfiedRequirement):
        moduleA.container.injector.get(Foo1)


def test_module_forward_ref_circular_dependencies():
    @Module(
        name="moduleA",
        modules=[ForwardRefModule(module_name="moduleB")],
        providers=[
            ProviderConfig(IRepository, use_class=FooDBCatsRepository),
            ProviderConfig(IDBContext, use_class=AnyDBContext),
        ],
        exports=[IRepository, IDBContext],
    )
    class ModuleA:
        pass

    @Module(
        name="moduleB",
        modules=[ForwardRefModule(module_name="moduleA")],
        providers=[ProviderConfig(Foo1, use_value=Foo1(), export=True)],
    )
    class ModuleB:
        pass

    app = Test.create_test_module(modules=[ModuleA, ModuleB]).create_application()
    assert isinstance(app.injector.get(IRepository), IRepository)
    assert isinstance(app.injector.get(IDBContext), IDBContext)

    moduleB = app.injector.tree_manager.get_module(ModuleB).value

    assert isinstance(moduleB.container.injector.get(IRepository), IRepository)
    assert isinstance(moduleB.container.injector.get(IDBContext), IDBContext)

    moduleA = app.injector.tree_manager.get_module(ModuleA).value

    moduleA.container.injector.get(Foo1)
