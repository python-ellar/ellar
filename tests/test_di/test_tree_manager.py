import pytest
from ellar.app import App
from ellar.common import Module
from ellar.core import Config, ModuleSetup
from ellar.di import MODULE_REF_TYPES
from ellar.di.injector import ModuleTreeManager
from ellar.utils import get_unique_type


def test_root_module_assert_should_raise_exception():
    tree_manager = ModuleTreeManager()

    with pytest.raises(AssertionError):
        assert tree_manager.root_module


def test_add_provider_fails_for_none_existing_module():
    tree_manager = ModuleTreeManager()

    module_type = get_unique_type("ModuleType")
    provider_type = get_unique_type("ProviderType")

    with pytest.raises(ValueError):
        tree_manager.add_provider(module_type, provider_type)


def test_add_provider_fails_if_the_module_is_module_setup_type():
    tree_manager = ModuleTreeManager()

    module_type = Module()(get_unique_type("ModuleType"))
    provider_type = get_unique_type("ProviderType")

    tree_manager.add_module(module_type, ModuleSetup(module_type))

    with pytest.raises(Exception, match=f"{str(module_type)} is not ready"):
        tree_manager.add_provider(module_type, provider_type)


def test_add_module_fails_for_already_existing_type():
    tree_manager = ModuleTreeManager()

    module_type = Module()(get_unique_type("ModuleType"))

    tree_manager.add_module(module_type, ModuleSetup(module_type))

    with pytest.raises(ValueError):
        tree_manager.add_module(module_type, ModuleSetup(module_type))


def test_add_module_fails_when_core_module_tries_to_have_more_than_one_dependency():
    core_module_type = ModuleSetup(Module()(get_unique_type("CoreModuleType")))
    tree_manager = ModuleTreeManager(core_module_type)

    module_type = Module()(get_unique_type("ModuleType"))

    tree_manager.add_module(module_type, ModuleSetup(module_type))

    with pytest.raises(ValueError):
        tree_manager.add_module(module_type, ModuleSetup(module_type))


def test_add_module_fails_when_parent_module_does_not_exist():
    tree_manager = ModuleTreeManager()

    module_type = Module()(get_unique_type("ModuleType"))
    parent_module_type = Module()(get_unique_type("ModuleType"))

    with pytest.raises(ValueError, match="Parent data for Module"):
        tree_manager.add_module(
            module_type, ModuleSetup(module_type), parent_module=parent_module_type
        )


def test_add_module_dependency_fails_when_parent_does_not_exist():
    tree_manager = ModuleTreeManager()

    parent_module_type = Module()(get_unique_type("ModuleType"))
    dependency_type = Module()(get_unique_type("DependencyType"))

    with pytest.raises(ValueError, match="Trying to add module dependency, Module"):
        tree_manager.add_module_dependency(parent_module_type, dependency_type)


def test_update_module_fails_if_module_type_does_exist():
    tree_manager = ModuleTreeManager()

    module_type = Module()(get_unique_type("ModuleType"))
    module_setup = ModuleSetup(module_type)

    with pytest.raises(
        ValueError, match=f"Module {module_type} does not exists. Use 'add_module'"
    ):
        tree_manager.update_module(module_type, module_setup)


def test_update_module_with_parent_changes_parent():
    tree_manager = ModuleTreeManager()

    module_type = Module()(get_unique_type("ModuleType"))
    parent_module_type = Module()(get_unique_type("ParentModuleType"))

    tree_manager.add_module(parent_module_type, ModuleSetup(parent_module_type))
    tree_manager.add_module(module_type, ModuleSetup(module_type), parent_module=None)

    tree_manager.update_module(
        module_type, ModuleSetup(module_type), parent_module=parent_module_type
    )
    assert tree_manager.get_module(module_type).parent == parent_module_type


def test_get_module_by_ref_type_works():
    tree_manager = ModuleTreeManager()

    module_type = Module()(get_unique_type("AppModuleType"))

    tree_manager.add_module(module_type, ModuleSetup(module_type))

    app_dependent_module = ModuleSetup(
        Module()(get_unique_type("AppModuleType")), inject=[App, Config]
    )
    tree_manager.add_module(
        app_dependent_module.module, app_dependent_module, module_type
    )

    items = tree_manager.get_by_ref_type(MODULE_REF_TYPES.DYNAMIC)
    assert len(items) == 1
    assert items[0].value.module == module_type

    items = tree_manager.get_by_ref_type(MODULE_REF_TYPES.APP_DEPENDENT)
    assert len(items) == 1
    assert items[0].value == app_dependent_module


def test_get_module_dependencies_return_empty_if_module_type_does_not_exist():
    tree_manager = ModuleTreeManager()

    module_type = Module()(get_unique_type("AppModuleType"))
    assert tree_manager.get_module_dependencies(module_type) == []


def test_find_module_returns_none_if_nothing_was_found():
    tree_manager = ModuleTreeManager()

    module_type = Module()(get_unique_type("AppModuleType"))
    assert (
        next(tree_manager.find_module(lambda data: data.value.module == module_type))
        is None
    )


def test_search_module_tree_works():
    core_module_type = ModuleSetup(Module()(get_unique_type("CoreModuleType")))
    tree_manager = ModuleTreeManager(core_module_type)

    app_module_type = Module()(get_unique_type("AppModuleType"))

    tree_manager.add_module(app_module_type, ModuleSetup(app_module_type))

    for _ in range(5):
        module_type = Module()(get_unique_type(f"ModuleType{_ + 1}"))
        tree_manager.add_module(module_type, ModuleSetup(module_type), app_module_type)

    for _ in range(5):
        module_type_ = Module()(get_unique_type(f"ModuleType{_ + 1}"))
        tree_manager.add_module(module_type_, ModuleSetup(module_type_), module_type)

    res = tree_manager.search_module_tree(
        lambda data: data.value.module == module_type,
        lambda data: data.value.module == module_type_,
    )
    assert res is not None
    assert res.parent == module_type
    assert res.value.module == module_type_


def test_find_module_return_list_of_items():
    core_module_type = ModuleSetup(Module()(get_unique_type("CoreModuleType")))
    tree_manager = ModuleTreeManager(core_module_type)

    app_module_type = Module()(get_unique_type("AppModuleType"))

    tree_manager.add_module(app_module_type, ModuleSetup(app_module_type))

    for _ in range(10):
        module_type = Module()(get_unique_type(f"ModuleType{_ + 1}"))
        tree_manager.add_module(module_type, ModuleSetup(module_type), app_module_type)

    res = list(
        tree_manager.find_module(
            lambda data: data.parent == app_module_type,
        )
    )

    assert len(res) == 10
    for item in res:
        assert item.parent == app_module_type
